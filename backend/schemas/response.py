from __future__ import annotations

from typing import Any, Generic, Optional, TypeVar
from pydantic import BaseModel

T = TypeVar("T")


class ErrorDetail(BaseModel):
    code: str
    details: Optional[Any] = None


class APIResponse(BaseModel, Generic[T]):
    success: bool
    message: str
    data: Optional[T] = None
    error: Optional[ErrorDetail] = None

    class Config:
        arbitrary_types_allowed = True


def success_response(data: Any = None, message: str = "Permintaan berhasil diproses") -> dict:
    """Helper untuk format JSON sukses konsisten."""
    resp = {
        "success": True,
        "message": message,
        "data": data if data is not None else {}
    }
    return resp


def error_response(code: str, message: str, details: Any = None) -> dict:
    """Helper untuk format JSON error konsisten."""
    err_obj = {"code": code}
    if details is not None:
        err_obj["details"] = details

    return {
        "success": False,
        "message": message,
        "error": err_obj
    }
