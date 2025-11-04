from typing import Any, Optional


def success(message: str = "ok", data: Optional[Any] = None) -> dict:
    return {"success": True, "message": message, "data": data}


def error(message: str, data: Optional[Any] = None) -> dict:
    return {"success": False, "message": message, "data": data}

