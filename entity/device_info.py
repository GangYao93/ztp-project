from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from database.database import Base


class DeviceInfo(Base):
    __tablename__ = 'device_info'
    # id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True,index=True)
    # mac = Column(String, unique=True, nullable=False)
    mac : Mapped[str] = mapped_column(autoincrement=False, index=True, unique=True, nullable=False)
    ip_address: Mapped[str] = mapped_column(autoincrement=False, index=True, unique=False, nullable=False)
    device_type: Mapped[str] = mapped_column(autoincrement=False, unique=False, nullable=False)
    os_type:Mapped[str] =  mapped_column(autoincrement=False, unique=False, nullable=False)
    status : Mapped[str] = mapped_column(autoincrement=False, unique=False, nullable=False)

