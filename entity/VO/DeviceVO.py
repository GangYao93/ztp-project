from typing import Any

from pydantic import BaseModel, Field


class DeviceRegister(BaseModel):
    mac: str
    ip_address: str
    os_type: str
    status: str
    device_type: str
    username: str | None = None
    password: str | None = None


class DeviceInfoQuery(BaseModel):
    mac: str | None = None
    ip_address: str | None = None
    device_type: str | None = None
    os_type: str | None = None
    status: str | None = None
    keyword: str | None = None
    page: int = Field(default=1, ge=1)
    size: int = Field(default=20, ge=1, le=100)


class DeviceConfigQuery(BaseModel):
    mac: str | None = None
    device_type: str | None = None
    os_type: str | None = None
    status: str | None = None
    keyword: str | None = None
    page: int = Field(default=1, ge=1)
    size: int = Field(default=20, ge=1, le=100)


class DeviceConfigSave(BaseModel):
    mac: str
    config_json: dict[str, Any]

