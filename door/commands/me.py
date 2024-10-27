from .base_command import BaseCommand


class AboutMe(BaseCommand):
    command = "me"
    description = "about you"
    help = "'Last heard' time is in UTC."

    def invoke(self, msg: str, node: str) -> str:
        u = self.get_node(node)

        reply = f"""Name: {u.user.longName} ({u.user.shortName})
Last heard: {u.last_heard.strftime("%Y-%m-%d %H:%M")}
SNR: {u.snr}
Hops: {u.hopsAway}"""

        if u.position:
            reply += f"""
Position: {u.position.latitude}, {u.position.longitude}, {u.position.altitude}
"""
        if u.deviceMetrics:
            reply += f"""
Device Metrics:
- battery: {u.deviceMetrics.batteryLevel}% {u.deviceMetrics.voltage} volts
- utilization: {u.deviceMetrics.channelUtilization} ({u.deviceMetrics.airUtilTx:.2})
- uptime: {u.deviceMetrics.uptimeSeconds}"""

        return reply
