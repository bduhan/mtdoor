from loguru import logger as log

from . import BaseCommand
from ..models import NodeInfo


def format_node_list(nodes: list[NodeInfo]) -> str:
    """
    output suitable for a list of nodes
    """
    response = ""
    n: NodeInfo
    for n in nodes:
        r = f"{n.user.id}: {n.user.longName} ({n.user.shortName})\n"

        if len(response) + len(r) > 200:
            break
        else:
            response += r

    return response.strip()


def format_node_detail(n: NodeInfo) -> str:
    """
    output for detail of a node
    """

    reply = f"""Name: {n.user.longName} ({n.user.shortName})
Last heard {n.last_heard.strftime("%Y-%m-%d %H:%M")}
SNR {n.snr}, Hops {n.hopsAway}"""

    if n.position:
        reply += f"""
Pos.: {n.position.latitude:.7}, {n.position.longitude:.8}, {n.position.altitude}
"""

    if n.deviceMetrics:
        reply += f"""
Batt.: {n.deviceMetrics.batteryLevel}% {n.deviceMetrics.voltage:.3}V
Util.: {n.deviceMetrics.channelUtilization} ch, {n.deviceMetrics.airUtilTx:.2} air
Up: {n.deviceMetrics.uptimeSeconds}s"""

    return reply


class NodeQuery(BaseCommand):
    command = "node"
    description = "read from my device node DB"
    help = "'node' for list\n'node <!id>' for detail\n'node me' for yours\n'node you' for mine"

    node_list_count: int = 5

    def invoke(self, msg: str, node: str) -> str:

        msg = msg[len(self.command) :].lstrip()

        # they want a list
        if msg == "":
            n: NodeInfo
            ns: list[NodeInfo] = []

            for n in self.interface.nodes.values():
                n = NodeInfo(**n)
                # don't show ourselves
                if n.user.id == self.interface.getMyUser()["id"]:
                    continue
                ns.append(n)
            return format_node_list(ns)

        # they want to know about themselves
        elif msg.strip().lower() == "me":
            n: NodeInfo = self.get_node(node)
            return format_node_detail(n)

        # they want to know about us
        elif msg.strip().lower() == "you":
            n = NodeInfo(**self.interface.getMyNodeInfo())
            return format_node_detail(n)

        # they want information about someone else
        else:
            try:
                n: NodeInfo = self.get_node(msg)
            except:
                log.exception(f"Failed to find node '{msg}'")

            if n:
                return format_node_detail(n)
            else:
                return "I can't find that node. Use the hex identifier that begins with '!'."
