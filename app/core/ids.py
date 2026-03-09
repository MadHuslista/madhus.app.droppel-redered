"""Stable identity models and helpers."""

from __future__ import annotations

import re

from pydantic import BaseModel, Field, validator


SLUG_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]*$")
SOURCE_BUNDLE_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]*$")


class DocumentIdentity(BaseModel):
    """Stable renderer identity for one importable document variant."""

    class Config:
        extra = "forbid"
        allow_mutation = False

    tenant_id: str = Field(..., description="User or workspace owner")
    document_id: str = Field(..., description="Stable renderer document ID")
    document_family_id: str = Field(..., description="Audio/source family identifier")
    variant_id: str = Field(..., description="Variant letter within a sample family")
    source_bundle_id: str = Field(..., description="Canonical source bundle ID")

    @validator("tenant_id", "document_id", "document_family_id", "variant_id")
    def validate_slug_identifier(cls, value: str) -> str:
        if not SLUG_PATTERN.fullmatch(value):
            msg = f"invalid identifier: {value!r}"
            raise ValueError(msg)
        return value

    @validator("source_bundle_id")
    def validate_source_bundle_id(cls, value: str) -> str:
        if not SOURCE_BUNDLE_PATTERN.fullmatch(value):
            msg = f"invalid identifier: {value!r}"
            raise ValueError(msg)
        return value