"""Tiny in-process background scheduler.

No Celery / cron dependency - a single asyncio task ticks every 60 seconds and
drives the time-based housekeeping that nothing else in the request/response
cycle would otherwise trigger: invitation expiry, approval reminders and
escalation. Every tick is wrapped in try/except so one bad row never kills the
loop for the rest of the process lifetime.
"""

import asyncio
from typing import Optional

from config.settings import settings
from core.logger.structured import get_logger
from repositories import approvals as approvals_repo
from services.approvals import ApprovalService
from services.invitations import InvitationService

logger = get_logger(__name__)

TICK_SECONDS = 60
MAX_REMINDERS = 3


class BackgroundScheduler:
    """Idempotent asyncio-task-based scheduler for time-based housekeeping."""

    _task: Optional[asyncio.Task] = None

    @classmethod
    async def start(cls) -> None:
        if cls._task is not None and not cls._task.done():
            logger.debug("Scheduler already running; start() is a no-op")
            return
        cls._task = asyncio.create_task(cls._loop())
        logger.info("Background scheduler started", context={"interval_seconds": TICK_SECONDS})

    @classmethod
    async def stop(cls) -> None:
        if cls._task is None:
            return
        cls._task.cancel()
        try:
            await cls._task
        except asyncio.CancelledError:
            pass
        finally:
            cls._task = None
        logger.info("Background scheduler stopped")

    @classmethod
    async def _loop(cls) -> None:
        while True:
            try:
                await cls._tick()
            except asyncio.CancelledError:
                raise
            except Exception as exc:  # pragma: no cover - the loop must never die
                logger.error("Scheduler tick failed", exc_info=exc)
            await asyncio.sleep(TICK_SECONDS)

    @classmethod
    async def _tick(cls) -> None:
        try:
            await InvitationService.expire_stale()
        except Exception as exc:
            logger.error("Failed to expire stale invitations", exc_info=exc)

        try:
            reminder_candidates = await approvals_repo.list_stale(settings.approval_reminder_seconds)
            for approval in reminder_candidates:
                if int(approval.get("reminder_count") or 0) < MAX_REMINDERS:
                    await ApprovalService.send_reminder(approval)
        except Exception as exc:
            logger.error("Failed to send approval reminders", exc_info=exc)

        try:
            escalation_candidates = await approvals_repo.list_stale(settings.escalation_timeout_seconds)
            for approval in escalation_candidates:
                await ApprovalService.escalate(approval)
        except Exception as exc:
            logger.error("Failed to escalate stale approvals", exc_info=exc)
