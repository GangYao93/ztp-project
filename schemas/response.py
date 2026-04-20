from pydantic import BaseModel
from typing import Generic, TypeVar, Optional

T = TypeVar('T')


class Response(BaseModel, Generic[T]):
    code: int
    msg: str
    data: Optional[T] = None

    @classmethod
    def success(cls,data=None):
        return cls(code=200, msg='success', data=data)

    @classmethod
    def fail(cls,data=None):
        return cls(code=500, msg='fail', data=data)
