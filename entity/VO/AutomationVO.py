from typing import Any

from pydantic import BaseModel, Field


class PlaybookQuery(BaseModel):
    name: str | None = None
    version: int | None = Field(default=None, ge=1)
    is_active: bool | None = None
    keyword: str | None = None
    page: int = Field(default=1, ge=1)
    size: int = Field(default=20, ge=1, le=100)


class PlaybookSave(BaseModel):
    id: int | None = Field(default=None, ge=1)
    name: str = Field(min_length=1)
    version: int = Field(ge=1)
    content: str = Field(min_length=1)
    is_active: bool = True


class AnsibleEnvQuery(BaseModel):
    name: str | None = None
    version: int | None = Field(default=None, ge=1)
    is_active: bool | None = None
    keyword: str | None = None
    page: int = Field(default=1, ge=1)
    size: int = Field(default=20, ge=1, le=100)


class AnsibleEnvSave(BaseModel):
    id: int | None = Field(default=None, ge=1)
    name: str = Field(min_length=1)
    version: int = Field(ge=1)
    env_json: dict[str, Any]
    is_active: bool = True


class DeviceProfileQuery(BaseModel):
    device_type: str | None = None
    os_type: str | None = None
    playbook_id: int | None = Field(default=None, ge=1)
    ansible_env_id: int | None = Field(default=None, ge=1)
    keyword: str | None = None
    page: int = Field(default=1, ge=1)
    size: int = Field(default=20, ge=1, le=100)


class DeviceProfileSave(BaseModel):
    id: int | None = Field(default=None, ge=1)
    device_type: str = Field(min_length=1)
    os_type: str = Field(min_length=1)
    playbook_id: int = Field(ge=1)
    ansible_env_id: int = Field(ge=1)
