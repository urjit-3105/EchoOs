"""Loads and serves workflow template YAML definitions.

Templates live under ``backend/config/workflows/*.yaml`` (see
``config/workflows/employee_onboarding.yaml``). The path is resolved relative
to this file - not the process cwd - so ``load_all()`` works whether the app
is started from ``backend/`` (the normal case) or from anywhere else.
"""

import os
from typing import Any, Dict, List

import yaml

from config.settings import settings
from core.logger.structured import get_logger

logger = get_logger(__name__)

_TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "config", "workflows")


class WorkflowTemplateRegistry:
    """Class-level cache of every workflow template definition, keyed by ``id``."""

    _templates: Dict[str, Dict[str, Any]] = {}
    _loaded: bool = False

    # ------------------------------------------------------------------
    # Loading
    # ------------------------------------------------------------------
    @classmethod
    def load_all(cls) -> Dict[str, Dict[str, Any]]:
        """Load every ``*.yaml`` file in the templates directory. Idempotent."""
        if cls._loaded:
            return cls._templates

        directory = os.path.normpath(_TEMPLATES_DIR)
        if not os.path.isdir(directory):
            logger.warning("Workflow templates directory not found.", context={"directory": directory})
            cls._loaded = True
            return cls._templates

        for filename in sorted(os.listdir(directory)):
            if not filename.endswith(".yaml") and not filename.endswith(".yml"):
                continue
            path = os.path.join(directory, filename)
            try:
                with open(path, "r") as handle:
                    definition = yaml.safe_load(handle)
                if not definition or "id" not in definition:
                    logger.warning("Skipping workflow template without an 'id'.", context={"file": filename})
                    continue
                cls._templates[definition["id"]] = definition
                logger.info("Loaded workflow template.", context={"key": definition["id"], "file": filename})
            except Exception as exc:  # noqa: BLE001 - one bad file shouldn't break startup
                logger.error("Failed to load workflow template.", context={"file": filename, "error": str(exc)})

        cls._loaded = True
        return cls._templates

    # ------------------------------------------------------------------
    # Accessors
    # ------------------------------------------------------------------
    @classmethod
    def keys(cls) -> List[str]:
        cls.load_all()
        return list(cls._templates.keys())

    @classmethod
    def get(cls, key: str) -> Dict[str, Any]:
        cls.load_all()
        if key not in cls._templates:
            raise ValueError(f"Unknown workflow template '{key}'.")
        return cls._templates[key]

    @classmethod
    def list(cls) -> List[Dict[str, Any]]:
        """Summaries suitable for a template picker in the UI."""
        cls.load_all()
        summaries = []
        for key, definition in cls._templates.items():
            summaries.append(
                {
                    "key": key,
                    "name": definition.get("name", key),
                    "description": definition.get("description", ""),
                    "version": definition.get("version", "1.0.0"),
                    "task_count": len(definition.get("tasks", [])),
                    "stages": definition.get("stages", []),
                }
            )
        return summaries

    @classmethod
    def register(cls, key: str, definition: Dict[str, Any]) -> None:
        """Register (or overwrite) a template at runtime, e.g. via an admin API."""
        cls.load_all()
        cls._templates[key] = definition
        logger.info("Registered workflow template at runtime.", context={"key": key})

    @classmethod
    def default(cls) -> Dict[str, Any]:
        return cls.get(settings.default_workflow_template)

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------
    @classmethod
    async def sync_to_database(cls) -> None:
        """Upsert every loaded template into the ``workflow_templates`` table."""
        cls.load_all()
        try:
            from repositories.workflow_templates import workflow_templates
        except Exception as exc:  # noqa: BLE001 - repository package may not be wired up yet
            logger.error("Could not import workflow_templates repository.", context={"error": str(exc)})
            return

        for key, definition in cls._templates.items():
            try:
                await workflow_templates.upsert_by(
                    "key",
                    key,
                    {
                        "name": definition.get("name", key),
                        "description": definition.get("description", ""),
                        "version": definition.get("version", "1.0.0"),
                        "definition": definition,
                        "is_active": True,
                    },
                )
            except Exception as exc:  # noqa: BLE001 - persistence must never crash startup
                logger.error(
                    "Failed to sync workflow template to database.",
                    context={"key": key, "error": str(exc)},
                )
