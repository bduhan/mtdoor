from . import BaseCommand


class Ping(BaseCommand):
    command = "ping"
    description = "'ping' replies with signal strength data"
    help = "This could be useful to test connectivity."

    def invoke(self, msg: str, node: str, packet) -> str:
        snr = packet.get("rxSnr", None)
        rssi = packet.get("rxRssi", None)
        hopStart = packet.get("hopStart", None)
        hopLimit = packet.get("hopLimit", None)

        response = f"Received ping from node {node}\n"
        if hopStart and hopLimit:
            hops = packet["hopStart"] - packet["hopLimit"]
            response += f"Hops: {hops}\n"
        if snr:
            response += f"SNR: {snr}\n"
        if rssi:
            response += f"RSSI: {rssi}"

        return response
