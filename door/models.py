"""
Some pydantic models for Meshtastic.
"""

import datetime
from typing import Optional
from pydantic import BaseModel, computed_field
import pytz

class UserInfo(BaseModel):
    id: str
    longName: Optional[str] = None
    shortName: Optional[str] = None
    macaddr: Optional[str] = None
    hwModel: Optional[str] = None
    publicKey: Optional[str] = None

class Position(BaseModel):
    latitude: float
    longitude: float
    altitude: Optional[int]
    time: Optional[int]

    @computed_field
    @property
    def timestamp(self) -> datetime.datetime:
        return datetime.datetime.fromtimestamp(self.time, pytz.UTC)

class DeviceMetrics(BaseModel):
    batteryLevel: Optional[int] = None
    voltage: Optional[float] = None
    channelUtilization: Optional[float] = None
    airUtilTx: Optional[float] = None
    uptimeSeconds: Optional[int] = None


class Node(BaseModel):
    num: int 
    snr: Optional[float] = None
    hopsAway: Optional[int] = None
    lastHeard: Optional[int] = None

    user: Optional[UserInfo] = None
    position: Optional[Position] = None
    deviceMetrics: Optional[DeviceMetrics] = None

    @computed_field
    @property
    def last_heard(self) -> datetime.datetime:
        return datetime.datetime.fromtimestamp(self.lastHeard, pytz.UTC)
