"""Document repository boundary."""

from __future__ import annotations

from typing import Protocol

from app.core.contracts.document_manifest import DocumentManifest


class DocumentRepository(Protocol):
    def list_documents(self, tenant_id: str) -> list[DocumentManifest]: ...

    def get_document(self, tenant_id: str, document_id: str) -> DocumentManifest | None: ...