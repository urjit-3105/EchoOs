"""Non-secret runtime settings, feature flags and compliance rules."""

import os
from typing import Any, Dict

import yaml
from fastapi import APIRouter, Body, Depends, HTTPException

from config.settings import settings
from core.logger.structured import get_logger
from core.verification.rules import RuleEngine
from repositories import organizations as organizations_repo
from routes.deps import get_current_org
from services.audit import AuditService

logger = get_logger(__name__)

router = APIRouter(prefix="/settings", tags=["Settings"])

_RULES_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config", "rules.yaml")


@router.get("/")
async def get_settings() -> Dict[str, Any]:
    """Safe, non-secret runtime settings + feature flags + compliance rules."""
    if not RuleEngine._rules:
        RuleEngine.load_rules()

    return {
        "app_name": settings.app_name,
        "environment": settings.environment,
        "api_v1_str": settings.api_v1_str,
        "frontend_url": settings.frontend_url,
        "default_workflow_template": settings.default_workflow_template,
        "max_retries": settings.max_retries,
        "retry_backoff_factor": settings.retry_backoff_factor,
        "escalation_timeout_seconds": settings.escalation_timeout_seconds,
        "approval_reminder_seconds": settings.approval_reminder_seconds,
        "require_manager_approval": settings.require_manager_approval,
        "invitation_expiry_hours": settings.invitation_expiry_hours,
        "feature_flags": {
            "enable_email": settings.enable_email,
            "enable_realtime": settings.enable_realtime,
            "enable_langgraph": settings.enable_langgraph,
            "enable_langfuse": settings.enable_langfuse,
            "enable_google_calendar": settings.enable_google_calendar,
            "enable_slack": settings.enable_slack,
            "enable_jira": settings.enable_jira,
            "enable_seed": settings.enable_seed,
        },
        "rules": RuleEngine._rules,
    }


@router.patch("/")
async def update_settings(
    payload: Dict[str, Any] = Body(...),
    org: Dict[str, Any] = Depends(get_current_org),
) -> Dict[str, Any]:
    """Update the current organization's `settings`/`policies` JSON blobs."""
    updates: Dict[str, Any] = {}
    if "settings" in payload:
        merged = dict(org.get("settings") or {})
        merged.update(payload["settings"] or {})
        updates["settings"] = merged
    if "policies" in payload:
        merged_policies = dict(org.get("policies") or {})
        merged_policies.update(payload["policies"] or {})
        updates["policies"] = merged_policies

    if not updates:
        raise HTTPException(status_code=400, detail="Provide 'settings' and/or 'policies' to update.")

    updated = await organizations_repo.update(org["id"], updates)
    await AuditService.record(
        "organization.settings_updated", "organization", org["id"], organization_id=org["id"], changes=updates
    )
    return updated or org


@router.get("/rules")
async def get_rules() -> Dict[str, Any]:
    """The active compliance rules loaded from config/rules.yaml."""
    if not RuleEngine._rules:
        RuleEngine.load_rules()
    return RuleEngine._rules


@router.put("/rules")
async def put_rules(payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    """Overwrite config/rules.yaml and reload it through the RuleEngine loader."""
    try:
        with open(_RULES_PATH, "w") as handle:
            yaml.safe_dump(payload, handle, sort_keys=False)
    except OSError as exc:
        raise HTTPException(status_code=500, detail=f"Failed to write rules.yaml: {exc}") from exc

    RuleEngine.load_rules()
    await AuditService.record("rules.updated", "settings", "rules.yaml")
    return RuleEngine._rules
