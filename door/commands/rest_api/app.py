from typing import Union
from functools import partial

from fastapi import FastAPI, APIRouter, Request, Depends, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.security import APIKeyHeader

from meshtastic import BROADCAST_ADDR
from meshtastic.mesh_interface import MeshInterface
from meshtastic.protobuf.mesh_pb2 import MeshPacket
from google.protobuf.json_format import MessageToDict

from ...models import NodeInfo


app = FastAPI(
    title="Meshtastic REST API", description="Operate a Meshtastic node with HTTP."
)

node = APIRouter(prefix="/nodes", tags=["nodes"])
messages = APIRouter(prefix="/messages", tags=["messages"])


# support simple API key
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=True)


def validate_api_key(
    actual_api_key: str, request_api_key: str = Depends(api_key_header)
):
    if actual_api_key != request_api_key:
        raise HTTPException(401, "Invalid API key")


def get_interface(request: Request) -> MeshInterface:
    """ Dependency for request handlers that need the mesh interface. """
    if "interface" in request.app.extra:
        interface: MeshInterface = request.app.extra["interface"]
        if not interface.isConnected.is_set():
            raise HTTPException(500, "Mesh interface is not connected.")
        return interface
    raise HTTPException(500, "Mesh interface not found.")


@app.get("/", include_in_schema=False)
def to_docs():
    "Redirect / to docs"
    return RedirectResponse(url="/docs")


@node.get("/")
def list_nodes(interface: MeshInterface = Depends(get_interface)) -> list[NodeInfo]:
    result: list[NodeInfo] = []
    for node_id, node in interface.nodes.items():
        ni = NodeInfo(**node)
        ni.id = node_id
        result.append(ni)
    return result


@node.get("{node_id}")
def get_node(
    node_id: str, interface: MeshInterface = Depends(get_interface)
) -> NodeInfo:
    if node_id in interface.nodes:
        return NodeInfo(**interface.nodes[node_id])
    return {}


# @app.get("/module_config", tags=["node"])
# def module_config():
#     pass


# send text
@messages.post("/text", tags=["messages"])
def send_text(
    text: str,
    destinationId: str = BROADCAST_ADDR,
    wantAck: bool = False,
    interface: MeshInterface = Depends(get_interface),
) -> dict:
    "Send text to a specific node or all."
    packet: MeshPacket = interface.sendText(text, destinationId, wantAck)
    return MessageToDict(packet, False)


# send telemetry
@messages.post("/telemetry", tags=["messages"])
def send_telemetry(
    destinationId: str = BROADCAST_ADDR,
    interface: MeshInterface = Depends(get_interface),
):
    """
    Trigger sending default telemetry data to specific node or all. There is no response to this.
    """
    # does not return the packet sent
    interface.sendTelemetry(destinationId)


# send position
@messages.post("/position", tags=["messages"])
def send_position(
    latitude: float = 0,
    longitude: float = 0,
    altitude: int = 0,
    destinationId: str = BROADCAST_ADDR,
    wantAck: bool = False,
    interface: MeshInterface = Depends(get_interface),
) -> dict:
    "Send position to specific node or all."
    packet: MeshPacket = interface.sendPosition(
        latitude=latitude,
        longitude=longitude,
        altitude=altitude,
        destinationId=destinationId,
        wantAck=wantAck,
    )
    return MessageToDict(packet)


def run(interface: MeshInterface, host: str, port: int, api_key: str = None):
    import uvicorn

    app.include_router(node)

    if api_key:
        validator = partial(validate_api_key, api_key)
        new_router = APIRouter(dependencies=[Depends(validator)])
        new_router.include_router(messages)
        app.include_router(new_router)
    else:
        app.include_router(messages)

    app.extra["interface"] = interface
    uvicorn.run(app, host=host, port=port, workers=1)
