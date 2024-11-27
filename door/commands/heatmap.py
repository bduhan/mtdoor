# This file adds a command to the mtdoor node-bot
# It loads a web server on startup and renders a
# HTML page when the command is invoked. The page
# will display a map centered on the node's GPS
# location and will display a heatmap of the other
# nodes in the node list representing their observed
# Signal Strength.
# Sending 'heatmap' to the node will return a
# Meshtastic message containing the URL of the
# Web server.
# Add the following lines to config.ini
# [door.commands.heatmap]
# heatmap_url = https://localhost:8080
# heatmap_port = 8080

import threading
import logging
from . import BaseCommand, CommandRunError, CommandLoadError
from loguru import logger as log
import time
from datetime import datetime, timedelta
import pytz
from pubsub import pub
import json

# Catch import errors for packges not required
# by previous versions of mtdoor that may not
# be installed. Run 'pip install -r requirements.txt'
import_errors = []
try:
    import folium
    from folium.plugins import HeatMap
    from folium.features import DivIcon
except ImportError as e:
    log.warning(f"{e} - Please run pip install folium")
    import_errors.append(e)

try:
    from flask import Flask, render_template_string, request, url_for, redirect

    app = Flask(__name__)
except ImportError as e:
    log.warning(f"{e} - Please run pip install flask")
    import_errors.append(e)

try:
    import netifaces
except ImportError as e:
    log.warning(f"{e} - Please run pip install netifaces")
    import_errors.append(e)

try:
    from timezonefinder import TimezoneFinder
except ImportError as e:
    log.warning(f"{e} - Please run pip install timezonefinder")
    import_errors.append(e)


class Heatmap(BaseCommand):
    command = "heatmap"
    description = "Generate a web-based heatmap of Meshtastic nodes"
    help = "heatmap - displays the URL of the web server"

    def load(self):
        """Load configuration values and prepare server thread without starting."""
        for error in import_errors:
            raise CommandLoadError(error)

        self.server_thread = None
        my_ip = self.get_local_ip()
        self.port = self.get_setting(int, "port", 5000)
        self.url = self.get_setting(str, "url", f"http://{my_ip}:{self.port}")

        # Set up route for rendering map
        app.route("/")(self.render_map)
        self.start_server()

        self.latitude, self.longitude = self.get_coordinates()
        if self.latitude and self.longitude:
            tf = TimezoneFinder()
            self.local_tz = pytz.timezone(
                tf.timezone_at(lng=self.longitude, lat=self.latitude)
            )
        else:
            self.local_tz = pytz.timezone("America/Chicago")

    def invoke(self, msg, node):
        """Handle command"""
        return f"View the heatmap for this node at {self.url}"

    def get_local_ip(self):
        for interface in netifaces.interfaces():
            addrs = netifaces.ifaddresses(interface)
            if netifaces.AF_INET in addrs:
                for addr in addrs[netifaces.AF_INET]:
                    if not addr["addr"].startswith("127."):
                        return addr["addr"]
        return "127.0.0.1"

    def get_coordinates(self):
        n = self.interface.getMyNodeInfo()
        if (
            n.get("position")
            and "latitude" in n["position"]
            and "longitude" in n["position"]
        ):
            latitude = self.interface.getMyNodeInfo()["position"]["latitude"]
            longitude = self.interface.getMyNodeInfo()["position"]["longitude"]
        else:
            latitude = self.get_setting(str, "default_latitude", None)
            longitude = self.get_setting(str, "default_longitude", None)
        return float(latitude), float(longitude)

    def format_time(self, seconds):
        if seconds < 60:
            return f"{seconds} seconds"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            return f"{minutes} minute{'s' if minutes > 1 else ''}"
        elif seconds < 86400:
            hours = int(seconds // 3600)
            return f"{hours} hour{'s' if hours > 1 else ''}"
        else:
            days = int(seconds // 86400)
            return f"{days} day{'s' if days > 1 else ''}"

    def start_server(self):
        """Start the Flask server in a new thread."""
        self.server_thread = threading.Thread(target=self._run_server)
        self.server_thread.daemon = True
        self.server_thread.start()
        log.info("Heatmap server started.")

    def _run_server(self):
        """Run the Flask server."""
        app.run(host="0.0.0.0", port=self.port)

    def render_map(self):
        """Render the heatmap using data from the node list."""

        myNodeId = self.interface.getMyUser()["id"]
        myLongName = self.interface.getMyUser()["longName"]
        myShortName = self.interface.getMyUser()["shortName"]
        title = f"Meshtastic Node Heatmap for {myLongName} ({myShortName})"
        show_all = request.args.get("show_all", "false").lower() == "true"
        seconds_in_1year = 60 * 60 * 24 * 365
        max_age = int(request.args.get("max_age", seconds_in_1year))
        base_map = folium.Map(location=[self.latitude, self.longitude], zoom_start=10)

        nodes = []
        for node in self.interface.nodes.values():
            node_data = {}
            node_data["num"] = node.get("num", None)
            if "user" in node:
                node_data["id"] = node["user"].get("id", None)
                node_data["longName"] = node["user"].get("longName", None)
                node_data["shortName"] = node["user"].get("shortName", None)
                node_data["hwModel"] = node["user"].get("hwModel", None)
                node_data["role"] = node["user"].get("role", None)
            else:
                node_data["id"] = None
                node_data["longName"] = None
                node_data["shortName"] = None
                node_data["hwModel"] = None
                node_data["role"] = None
            node_data["snr"] = node.get("snr", None)
            node_data["hopsAway"] = node.get("hopsAway", None)
            if node_data["shortName"] == myShortName:
                node_data["hopsAway"] = 0
                node_data["snr"] = 10
            node_data["lastHeard"] = node.get("lastHeard", None)
            if "position" in node:
                node_data["latitude"] = node["position"].get("latitude", None)
                node_data["longitude"] = node["position"].get("longitude", None)
            else:
                node_data["latitude"] = None
                node_data["longitude"] = None
            if (
                node_data["id"] == myNodeId
                and not node_data["latitude"]
                and not node_data["longitude"]
            ):
                node_data["latitude"] = self.latitude
                node_data["longitude"] = self.longitude

            timestamp = ""
            if node_data["lastHeard"]:
                node_data["timestamp"] = (
                    f"{datetime.fromtimestamp(node_data['lastHeard'], self.local_tz).strftime('%Y-%m-%d %H:%M:%S')}"
                )
                node_data["age"] = (
                    f"{self.format_time(int(time.time()) - node_data['lastHeard'])} ago"
                )
            else:
                node_data["timestamp"] = None
                node_data["age"] = None

            text_width = len(node_data["shortName"]) * 10.5
            tooltip = f"{node_data['longName']}"
            if node_data["hwModel"] and node_data["hwModel"] != "UNSET":
                tooltip += f"\n{node_data['hwModel']}"
            if node_data["hopsAway"] == 0:
                tooltip += f"\nSNR: {node_data['snr']}"
            else:
                tooltip += f"\nHops: {node_data['hopsAway']}"
            tooltip += f"\n{node_data['timestamp']}"

            if (
                node_data["latitude"]
                and node_data["longitude"]
                and (
                    (
                        (node_data["hopsAway"] == 0 or show_all)
                        and node_data["lastHeard"] != None
                        and datetime.now()
                        - datetime.fromtimestamp(node_data["lastHeard"])
                        < timedelta(seconds=max_age)
                    )
                    or node_data["id"] == myNodeId
                )
            ):
                folium.map.Marker(
                    location=[node_data["latitude"], node_data["longitude"]],
                    icon=DivIcon(
                        icon_size=(text_width, 36),
                        html=(
                            f'<div title="{tooltip}{timestamp}" '
                            f'style="font-size: 18px; color: blue; '
                            f'text-shadow: 0px 0px 10px rgba(255, 255, 255, 0.7);">'
                            f'{node_data["shortName"]}'
                            "</div>"
                        ),
                    ),
                ).add_to(base_map)

            nodes.append(node_data)

        heat_data = [
            [node["latitude"], node["longitude"], (node["snr"] + 20) / 30]
            for node in nodes
            if (
                (
                    (
                        node["lastHeard"] != None
                        and datetime.now() - datetime.fromtimestamp(node["lastHeard"])
                        < timedelta(seconds=max_age)
                    )
                    or node["id"] == myNodeId
                )
                and node["hopsAway"] == 0
                and node["latitude"]
                and node["longitude"]
                and node["snr"] is not None
            )
        ]
        folium.plugins.HeatMap(heat_data).add_to(base_map)

        folium.plugins.Fullscreen(
            position="topright",
            title="Full Screen",
            title_cancel="Exit Full Screen",
            force_separate_button=True,
        ).add_to(base_map)

        # Sort nodes and filter by time difference
        sorted_nodes = sorted(
            [item for item in nodes if item["lastHeard"]],
            key=lambda item: item["lastHeard"],
            reverse=True,
        )
        map_html = base_map._repr_html_()
        return render_template_string(
            MAP_HTML,
            title=title,
            map_html=map_html,
            show_all=show_all,
            max_age=max_age,
            node_data=sorted_nodes,
        )


MAP_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <link rel="icon" type="image/x-icon" href="https://meshtastic.letstalkthis.com/wp-content/uploads/2022/02/Favicon2.jpg">
    <style>
        body {
            font-family: Arial, sans-serif;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            margin: 0;
            padding: 0;
        }

        h1 {
            font-size: 2rem;
            margin: 20px;
            text-align: center;
        }

        #map {
            width: 90%; /* Make map fill the available width */
            aspect-ratio: 5 / 3;
            border-radius: 8px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
            max-height: 100vh; /* Prevent the map from exceeding the viewport height */
            min-height: 0; /* Ensure no minimum height is enforced */
        }

        #table-container {
            width: 100%;
            overflow-x: auto; /* Allow horizontal scrolling */
            margin-top: 20px;
        }

        table {
            border-collapse: collapse;
            width: 100%; /* Ensure table adapts to container width */
            min-width: 600px; /* Prevent the table from being too narrow */
        }

        th, td {
            padding: 12px 20px; /* Adjust padding for readability */
            border: 1px solid #ddd;
            text-align: center;
            white-space: nowrap; /* Prevent text wrapping */
            overflow: hidden; /* Hide overflow if text exceeds width */
            text-overflow: ellipsis; /* Add ellipsis for long text */
        }

        th {
            background-color: #f4f4f4;
            font-weight: bold;
        }

        @media (max-width: 600px) {
            h1 {
                font-size: 1.5rem; /* Reduce font size for small screens */
            }
        }
    </style>
    <script>
        function updateControls() {
            let showAll = document.getElementById("showAllCheckbox").checked;
            let maxAge = document.getElementById("maxAge").value;
            window.location.href = `?show_all=${showAll}&max_age=${maxAge}`;
        }

        let refreshTimer;

        function setRefreshInterval() {
            const interval = parseInt(document.getElementById("refreshInterval").value);
            if (refreshTimer) clearInterval(refreshTimer);

            if (interval > 0) {
                refreshTimer = setInterval(() => {
                    location.reload();
                }, interval * 1000);  // Convert seconds to milliseconds
            }
        }

        document.addEventListener("DOMContentLoaded", function () {
            document.getElementById("refreshInterval").addEventListener("change", setRefreshInterval);
            document.getElementById("showAllCheckbox").addEventListener("change", updateControls);
            document.getElementById("maxAge").addEventListener("change", updateControls);
            setRefreshInterval();
        });
    </script>
</head>
<body>
    <h1>{{ title }}</h1>
    <!-- Refresh Interval Controls -->
    <div id="controls">
        <table><tr>
        <th>
        <label for="refreshInterval">Refresh every:</label>
        <select id="refreshInterval">
            <option value="0" selected>Off</option>
            <option value="60">1 minute</option>
            <option value="300">5 minutes</option>
            <option value="900">15 minutes</option>
            <option value="3600">1 hour</option>
        </select>
        </th>
        <th>
        <label>
            <input type="checkbox" id="showAllCheckbox" onchange="updateControls()" {% if show_all %} checked {% endif %}>
            Show nodes with hops > 0
        </label>
        </th>
        <th>
        <label for="maxAge">Max age:</label>
        <select id="maxAge" onchange="updateControls()">
            <option value="31536000" {% if max_age == 31536000 %} selected {% endif %}>None</option>
            <option value="3600" {% if max_age == 3600 %} selected {% endif %}>1 hour</option>
            <option value="43200" {% if max_age == 43200 %} selected {% endif %}>12 hours</option>
            <option value="86400" {% if max_age == 86400 %} selected {% endif %}>1 day</option>
            <option value="172800" {% if max_age == 172800 %} selected {% endif %}>2 days</option>
            <option value="604800" {% if max_age == 604800 %} selected {% endif %}>1 week</option>
        </select>
        </th>
        </tr></table>
    </div>
    <div id="map">
        {{ map_html|safe }}
    </div>
    <div id="table-container">
        <table>
            <thead>
                <tr>
                    <th>Node ID</th>
                    <th>Long Name</th>
                    <th>Short Name</th>
                    <th>Hardware</th>
                    <th>Hops Away</th>
                    <th>Latitude</th>
                    <th>Longitude</th>
                    <th>Last Heard</th>
                    <th>SNR</th>
                </tr>
            </thead>
            <tbody>
                {% for node in node_data %}
                <tr>
                    <td>{{ node['id'] }}</td>
                    <td>{{ node['longName'] }}</td>
                    <td>{{ node['shortName'] }}</td>
                    <td>{{ node['hwModel'] }}</td>
                    <td>{{ node['hopsAway'] }}</td>
                    <td>{{ node['latitude'] }}</td>
                    <td>{{ node['longitude'] }}</td>
                    <td>{{ node['timestamp'] | default("N/A") }}</td>
                    <td>{{ node['snr'] }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
</body>
</html>
"""
