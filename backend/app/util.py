"""Shared request helpers: strict base64 decoding and error types."""
import base64
import binascii

from fastapi import HTTPException


def b64decode(value: str, field: str) -> bytes:
    try:
        return base64.b64decode(value.encode(), validate=True)
    except (binascii.Error, ValueError):
        raise HTTPException(status_code=400, detail=f"Invalid base64 in field: {field}")


def b64encode(data: bytes) -> str:
    return base64.b64encode(data).decode()
