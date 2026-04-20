from pydantic import BaseModel


class DeviceRegister(BaseModel):
    mac: str
    ip_address: str
    os_type: str
    status: str
    device_type: str

