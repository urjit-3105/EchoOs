"""StoragePlugin - provisions workspaces and archives documents.

Uses the app's own storage abstraction (``database.db``) rather than a
third-party object store: whether that resolves to Supabase Storage or the
local filesystem fallback used by the SQL adapter is a deployment concern,
not a plugin concern.
"""

import json
from datetime import datetime
from typing import Any, Dict, List

from config.settings import settings
from core.execution.plugins.base import BasePlugin
from core.execution.registry import ToolRegistry
from core.logger.structured import get_logger

logger = get_logger(__name__)


def _mode_for_adapter(adapter_name: str) -> str:
    """Supabase Storage counts as 'live'; the local SQL adapter's filesystem fallback as 'local'."""
    if adapter_name == "supabase":
        return "live"
    if adapter_name == "sqlalchemy":
        return "local"
    return "simulated"


@ToolRegistry.register("storage")
class StoragePlugin(BasePlugin):
    """Provisions employee workspaces and archives documents via ``database.db``."""

    @property
    def tool_name(self) -> str:
        return "storage"

    async def connect(self) -> bool:
        return True

    async def validate(self, inputs: Dict[str, Any]) -> bool:
        action = inputs.get("action", "provision_workspace")
        if action == "upload":
            return bool(inputs.get("file_name")) and inputs.get("content") is not None
        return True

    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        action = inputs.get("action", "provision_workspace")
        try:
            if action == "upload":
                result = await self._upload(inputs)
            elif action == "archive_documents":
                result = await self._archive_documents(inputs)
            else:
                result = await self._provision_workspace(inputs)
            await self._audit(action, inputs, result)
            return result
        except Exception as exc:
            logger.error("Storage plugin execution failed", context={"action": action}, exc_info=exc)
            result = {"status": "failed", "mode": "simulated", "error": str(exc)}
            await self._audit(action, inputs, result)
            return result

    async def rollback(self, execution_data: Dict[str, Any]) -> bool:
        path = execution_data.get("path")
        if not path:
            return True
        try:
            from database import db

            return await db.delete_file(settings.supabase_storage_bucket, path)
        except Exception as exc:
            logger.error("Storage rollback (delete_file) failed", context={"path": path}, exc_info=exc)
            return False

    async def health(self) -> bool:
        return True

    # ------------------------------------------------------------------
    async def _provision_workspace(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        from database import db

        employee_id = inputs.get("employee_id", "unknown")
        employee_name = inputs.get("employee_name", "New Employee")
        department = inputs.get("department", "General")

        readme = (
            f"# Welcome, {employee_name}!\n\n"
            "This workspace was provisioned automatically by Echo WorkforceOS.\n\n"
            f"- Department: {department}\n"
            f"- Provisioned at: {datetime.utcnow().isoformat()}Z\n\n"
            "Use this space for onboarding documents, notes and personal files.\n"
        )
        path = f"workspaces/{employee_id}/README.md"
        url = await db.upload_file(settings.supabase_storage_bucket, path, readme.encode("utf-8"), "text/markdown")
        mode = _mode_for_adapter(getattr(db, "name", "simulated"))
        return {
            "status": "success",
            "mode": mode,
            "workspace_url": url,
            "path": path,
            "details": f"Provisioned workspace for {employee_name} ({mode}).",
        }

    async def _upload(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        from database import db

        file_name = inputs["file_name"]
        content = inputs["content"]
        if isinstance(content, str):
            content = content.encode("utf-8")
        employee_id = inputs.get("employee_id", "shared")
        path = f"uploads/{employee_id}/{file_name}"
        content_type = inputs.get("content_type", "application/octet-stream")

        url = await db.upload_file(settings.supabase_storage_bucket, path, content, content_type)
        mode = _mode_for_adapter(getattr(db, "name", "simulated"))
        return {
            "status": "success",
            "mode": mode,
            "file_url": url,
            "path": path,
            "details": f"Uploaded '{file_name}' ({mode}).",
        }

    async def _archive_documents(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        from database import db
        from repositories import documents as documents_repo

        employee_id = inputs.get("employee_id")
        rows: List[Dict[str, Any]] = []
        if employee_id:
            try:
                rows = await documents_repo.list_by_employee(employee_id)
            except Exception as exc:
                logger.warning(
                    "Could not load documents to archive", context={"employee_id": employee_id}, exc_info=exc
                )

        manifest = {
            "employee_id": employee_id,
            "archived_at": datetime.utcnow().isoformat() + "Z",
            "document_count": len(rows),
            "documents": [
                {
                    "id": row.get("id"),
                    "document_type": row.get("document_type"),
                    "file_name": row.get("file_name"),
                    "storage_url": row.get("storage_url"),
                }
                for row in rows
            ],
        }
        path = f"archives/{employee_id}/manifest.json"
        content = json.dumps(manifest, indent=2).encode("utf-8")
        url = await db.upload_file(settings.supabase_storage_bucket, path, content, "application/json")
        mode = _mode_for_adapter(getattr(db, "name", "simulated"))
        return {
            "status": "success",
            "mode": mode,
            "workspace_url": url,
            "path": path,
            "document_count": len(rows),
            "details": f"Archived {len(rows)} documents for employee {employee_id} ({mode}).",
        }

    async def _audit(self, action: str, inputs: Dict[str, Any], result: Dict[str, Any]) -> None:
        try:
            from services.audit import AuditService

            await AuditService.record(
                action=f"plugin.{self.tool_name}.{action}",
                resource_type="integration",
                resource_id=inputs.get("employee_id") or inputs.get("workflow_id") or "system",
                actor=self.tool_name,
                actor_type="agent",
                changes=result,
            )
        except Exception as exc:
            logger.warning("Failed to record audit trail for storage plugin", exc_info=exc)
