from loguru import logger as log

from .base_command import BaseCommand
from ..models import NodeInfo


def format_node_list(nodes: list[NodeInfo]) -> str:
    """
    output suitable for a list of nodes
    """
    response = ""
    n: NodeInfo
    for n in nodes:
        r = f"{n.last_heard.strftime('%m-%d %H:%M')}"
        if n.user:
            if n.user.id:
                r += f" ({n.user.id}"

            if n.user.shortName:
                r += f", {n.user.shortName})"
            else:
                r += ")"

            if n.user.longName:
                r += f", {n.user.longName}"

        r += f", {n.snr} snr, {n.hopsAway} hops"
        r += "\n\n"

        if len(response) + len(r) > 200:
            break
        else:
            response += r

    return response


def format_node_detail(n: NodeInfo) -> str:
    """
    output for detail of a node
    """

    reply = f"""Name: {n.user.longName} ({n.user.shortName})
Last heard: {n.last_heard.strftime("%Y-%m-%d %H:%M")}
SNR: {n.snr}
Hops: {n.hopsAway}"""

    if n.position:
        reply += f"""
Position: {n.position.latitude}, {n.position.longitude}, {n.position.altitude}
"""
    if n.deviceMetrics:
        reply += f"""
Device Metrics:
- battery: {n.deviceMetrics.batteryLevel}% {n.deviceMetrics.voltage} volts
- utilization: {n.deviceMetrics.channelUtilization} ({n.deviceMetrics.airUtilTx:.2})
- uptime: {n.deviceMetrics.uptimeSeconds}"""

    return reply


class NodeQuery(BaseCommand):
    command = "node"
    description = "read bot node DB"

    node_list_count: int = 5

    def invoke(self, msg: str, node: str) -> str:

        msg = msg[len(self.command) :].lstrip()

        # they want a list
        if msg == "":
            log.debug("list")
            n: NodeInfo
            ns: list[NodeInfo] = []

            for n in self.interface.nodes.values():
                ns.append(NodeInfo(**n))
                if len(ns) > self.node_list_count:
                    break
            return format_node_list(ns)

        # they want information about themselves
        elif msg.strip().lower() == "me":
            log.debug("me")
            n: NodeInfo = self.get_node(node)
            return format_node_detail(n)

        # they want information about someone else
        else:
            log.debug("else")
            try:
                n: NodeInfo = self.get_node(msg)
            except:
                log.exception(f"Failed to find node '{msg}'")
                return "I can't find that node."

            return format_node_detail(n)
