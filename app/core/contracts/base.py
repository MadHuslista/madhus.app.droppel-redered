"""Common utilities for frozen runtime contracts."""

from __future__ import annotations

from pydantic import BaseModel


class FrozenContract(BaseModel):
    class Config:
        extra = "forbid"
        allow_mutation = False