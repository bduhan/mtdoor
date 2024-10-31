"""
Some pydantic models for Meshtastic.
"""

import datetime
from typing import Optional
from pydantic import BaseModel, Field, AliasChoices, computed_field
import pytz


class UserInfo(BaseModel):
    """
    source: packet
    """
    id: str = Field(validation_alias=AliasChoices("id", "fromId"))
    longName: Optional[str] = None
    shortName: Optional[str] = None
    macaddr: Optional[str] = None
    hwModel: Optional[str] = None
    publicKey: Optional[str] = None


class Message(BaseModel):
    fromId: str
    toId: str
    payload: str


class Position(BaseModel):
    """
    source: packet or device node db
    """
    id: str = Field(validation_alias=AliasChoices("id", "fromId"), default=None)
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    altitude: Optional[int] = None
    time: Optional[int] = None
    satsInView: Optional[int] = None

    @computed_field
    @property
    def timestamp(self) -> datetime.datetime:
        if self.time:
            return datetime.datetime.fromtimestamp(self.time, pytz.UTC)


class DeviceMetric(BaseModel):
    """
    source: packet
    """
    id: str = Field(validation_alias=AliasChoices("id", "fromId"), default=None)
    batteryLevel: Optional[int] = None
    voltage: Optional[float] = None
    channelUtilization: Optional[float] = None
    airUtilTx: Optional[float] = None
    uptimeSeconds: Optional[int] = None

    time: Optional[int] = None

    @computed_field
    @property
    def timestamp(self) -> datetime.datetime:
        if self.time:
            return datetime.datetime.fromtimestamp(self.time, pytz.UTC)


class NodeInfo(BaseModel):
    """
    source: device node db
    """
    id: str = Field(validation_alias=AliasChoices("id"), default=None)
    snr: Optional[float] = None
    hopsAway: Optional[int] = None
    lastHeard: Optional[int] = None

    user: Optional[UserInfo] = None
    position: Optional[Position] = None
    deviceMetrics: Optional[DeviceMetric] = None

    @computed_field
    @property
    def last_heard(self) -> datetime.datetime:
        if self.lastHeard:
            return datetime.datetime.fromtimestamp(self.lastHeard, pytz.UTC)

# class DeviceMetric(BaseModel):
#     id: str = Field(validation_alias=AliasChoices("id", "fromId"))
#     time: int
#     batteryLevel: int
#     voltage: float
#     channel_utilization: float
#     air_util_tx: float
#     uptime_seconds: int

class EnvironmentMetric(BaseModel):
    """
    source: packet
    """
    id: str = Field(validation_alias=AliasChoices("id", "fromId"), default=None)
    time: Optional[int] = None
    temperature: Optional[float] = None
    relative_humidity: Optional[float] = None
    barometric_pressure: Optional[float] = None
    gas_resistance: Optional[float] = None
    voltage: Optional[float] = None
    current: Optional[float] = None
    iaq: Optional[int] = None
    distance: Optional[float] = None
    lux: Optional[float] = None
    white_lux: Optional[float] = None
    ir_lux: Optional[float] = None
    uv_lux: Optional[float] = None
    wind_direction: Optional[int] = None
    wind_speed: Optional[float] = None
    weight: Optional[float] = None
    wind_gust: Optional[float] = None
    wind_lull: Optional[float] = None

