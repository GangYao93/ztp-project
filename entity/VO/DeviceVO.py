from pydantic import BaseModel


class DeviceRegister(BaseModel):
    mac: str
    ip_address: str
    os_type: str
    status: str
    device_type: str
    ansible_user: str | None = None
    ansible_ssh_pass: str | None = None

