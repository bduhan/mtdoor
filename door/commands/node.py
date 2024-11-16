from loguru import logger as log

from . import BaseCommand
from ..models import NodeInfo


def format_node_list(nodes: list[NodeInfo], msg: str) -> str:
    """
    output suitable for a list of nodes
    """
    response = ""
    n: NodeInfo
    for n in nodes:
        if msg == "sn":    
            # Listing only short names will maximize the number of nodes in response
            r = f"{n.user.shortName}\n"    
        elif msg == "ln":
            # This gives more info but will limit the # of nodes in response
            r = f"{n.user.id}: {n.user.longName} ({n.user.shortName})\n"
        else:    
            # List only nodeId by default 
            r = f"{n.user.id}\n"

        if len(response) + len(r) > 200:
            break
        else:
            response += r

    return response.strip()


def format_node_detail(n: NodeInfo) -> str:
    """
    output for detail of a node
    """

    reply = f"ID: {n.user.id} "
    # Make sure each item is not None before trying to add it
    if n.user.longName and n.user.shortName:
        reply += f"Name: {n.user.longName} ({n.user.shortName})\n"
    if n.last_heard:
        reply += f"Last heard {n.last_heard.strftime('%Y-%m-%d %H:%M')}\n"
    if n.snr != None and n.hopsAway != None:
        reply += f"SNR {n.snr}, Hops {n.hopsAway}\n"
    if n.position:
        if n.position.latitude and n.position.longitude:
            reply += f"Pos.: {n.position.latitude:.7}, {n.position.longitude:.8}"
        if n.position.altitude:
            reply += f", {n.position.altitude}\n"
        else:
            reply += "\n"
    if n.deviceMetrics:
        if n.deviceMetrics.batteryLevel and n.deviceMetrics.voltage:
            reply += f"Batt.: {n.deviceMetrics.batteryLevel}% {n.deviceMetrics.voltage:.3}V\n"
        if n.deviceMetrics.channelUtilization and n.deviceMetrics.airUtilTx:
            reply += f"Util.: {n.deviceMetrics.channelUtilization} ch, {n.deviceMetrics.airUtilTx:.2} air\n"
        if n.deviceMetrics.uptimeSeconds:
            reply += f"Up: {format_time(n.deviceMetrics.uptimeSeconds)}"

    # In case we go over the size limit, truncate response
    return reply[:200]


def format_time(seconds: int) -> str:    
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


class NodeQuery(BaseCommand):
    command = "node"
    description = "Read from my device node DB"
    #help = "'node' for list\n'node <!id>' for detail\n'node me' for yours\n'node you' for mine"
    help = ("'node' or 'node id' for NodeID list\n'node sn' for short name list\n"
            "'node ln' for long names\n"
            "'node <!id>' or 'node <name> for detail\n'node me' for yours\n'node you' for mine")

    node_list_count: int = 5

    def invoke(self, msg: str, node: str) -> str:

        msg = msg[len(self.command) :].lstrip()

        # they want a list
        if msg in ["", "id", "sn", "ln"]:
            n: NodeInfo
            ns: list[NodeInfo] = []

            for n in self.interface.nodes.values():
                n = NodeInfo(**n)
                # don't show ourselves
                if n.user.id == self.interface.getMyUser()["id"]:
                    continue
                ns.append(n)
            return format_node_list(ns, msg)

        # they want to know about themselves
        elif msg.strip().lower() == "me":
            n: NodeInfo = self.get_node(node)
            return format_node_detail(n)

        # they want to know about us
        elif msg.strip().lower() == "you":
            n = NodeInfo(**self.interface.getMyNodeInfo())
            return format_node_detail(n)

        # they want to know about a short name
        elif msg.strip().lower()[:1] != "!":
            n: NodeInfo
            for n in self.interface.nodes.values():
                n = NodeInfo(**n)
                if n.user.shortName.strip().lower() == msg.strip().lower():
                    return format_node_detail(n)
            return "I can't find that node. Use the short name or the hex identifier that begins with '!'."

        # they want information about a node ID
        else:
            try:
                n: NodeInfo = self.get_node(msg)
            except:
                log.exception(f"Failed to find node '{msg}'")

            if n:
                return format_node_detail(n)
            else:
                return "I can't find that node. Use the short name or the hex identifier that begins with '!'."
