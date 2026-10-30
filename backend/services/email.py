"""Outbound email service.

Every email - real or simulated - is recorded in ``email_outbox`` first so the
UI always has something to show, even when SMTP is disabled (the default for
local development). When ``settings.smtp_enabled`` the message is additionally
delivered via ``smtplib`` on a thread executor so the async event loop never
blocks on network I/O.
"""

import asyncio
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict, Optional

from config.settings import settings
from core.logger.structured import get_logger
from repositories import email_outbox

logger = get_logger(__name__)


class EmailService:
    """Sends (or simulates) transactional email and keeps an outbox audit trail."""

    @staticmethod
    async def send(
        *,
        to: str,
        subject: str,
        html: Optional[str] = None,
        text: Optional[str] = None,
        template: Optional[str] = None,
    ) -> Dict[str, Any]:
        row = await email_outbox.create(
            {
                "to_email": to,
                "subject": subject,
                "body_text": text,
                "body_html": html,
                "template": template,
                "status": "queued",
            }
        )

        if not settings.smtp_enabled:
            simulated = await email_outbox.update(
                row["id"],
                {"status": "simulated", "provider": "outbox", "sent_at": datetime.utcnow().isoformat()},
            )
            logger.info("Email simulated (SMTP disabled)", context={"to": to, "subject": subject})
            return simulated or row

        try:
            await asyncio.get_event_loop().run_in_executor(
                None, EmailService._send_smtp, to, subject, html, text
            )
            sent = await email_outbox.update(
                row["id"],
                {"status": "sent", "provider": "smtp", "sent_at": datetime.utcnow().isoformat()},
            )
            logger.info("Email sent via SMTP", context={"to": to, "subject": subject})
            return sent or row
        except Exception as exc:  # pragma: no cover - network dependent
            logger.error("Failed to send email via SMTP", context={"to": to, "subject": subject}, exc_info=exc)
            failed = await email_outbox.update(
                row["id"], {"status": "failed", "provider": "smtp", "error_message": str(exc)}
            )
            return failed or row

    @staticmethod
    def _send_smtp(to: str, subject: str, html: Optional[str], text: Optional[str]) -> None:
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = settings.smtp_from
        message["To"] = to

        if text:
            message.attach(MIMEText(text, "plain"))
        if html:
            message.attach(MIMEText(html, "html"))
        if not text and not html:
            message.attach(MIMEText(subject, "plain"))

        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
            if settings.smtp_use_tls:
                server.starttls()
            if settings.smtp_user and settings.smtp_password:
                server.login(settings.smtp_user, settings.smtp_password)
            server.sendmail(settings.smtp_from, [to], message.as_string())

    # ------------------------------------------------------------------
    # Templates - simple inline-styled HTML, no external assets
    # ------------------------------------------------------------------
    @staticmethod
    def _wrap(title: str, body_html: str) -> str:
        return f"""
        <div style="font-family: -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif;
                    max-width: 560px; margin: 0 auto; padding: 24px; color: #1f2933;">
          <h2 style="color: #111827; margin-bottom: 16px;">{title}</h2>
          {body_html}
          <p style="margin-top: 32px; font-size: 12px; color: #9ca3af;">
            Sent by ECHO WorkforceOS &middot; automated message
          </p>
        </div>
        """

    @staticmethod
    def invitation_email(
        employee_name: str, org_name: str, accept_url: str, expires_at: str
    ) -> tuple[str, str]:
        subject = f"You're invited to join {org_name}"
        body = f"""
        <p>Hi {employee_name},</p>
        <p>Welcome to <strong>{org_name}</strong>! Your onboarding portal is ready.</p>
        <p style="margin: 24px 0;">
          <a href="{accept_url}" style="background:#2563eb;color:#fff;padding:12px 20px;
             border-radius:8px;text-decoration:none;font-weight:600;">Start Onboarding</a>
        </p>
        <p>This invitation expires on {expires_at}.</p>
        """
        return subject, EmailService._wrap(subject, body)

    @staticmethod
    def welcome_email(
        employee_name: str, org_name: str, corporate_email: str, portal_url: str
    ) -> tuple[str, str]:
        subject = f"Welcome to {org_name}!"
        body = f"""
        <p>Hi {employee_name},</p>
        <p>Your onboarding is complete and your account is active.</p>
        <p><strong>Corporate email:</strong> {corporate_email}</p>
        <p style="margin: 24px 0;">
          <a href="{portal_url}" style="background:#16a34a;color:#fff;padding:12px 20px;
             border-radius:8px;text-decoration:none;font-weight:600;">Open Your Portal</a>
        </p>
        """
        return subject, EmailService._wrap(subject, body)

    @staticmethod
    def approval_request_email(
        approver_name: str, employee_name: str, approval_url: str, reason: str
    ) -> tuple[str, str]:
        subject = f"Approval needed: {employee_name}'s onboarding"
        body = f"""
        <p>Hi {approver_name},</p>
        <p><strong>{employee_name}</strong>'s onboarding needs your sign-off.</p>
        <p><strong>Reason:</strong> {reason}</p>
        <p style="margin: 24px 0;">
          <a href="{approval_url}" style="background:#d97706;color:#fff;padding:12px 20px;
             border-radius:8px;text-decoration:none;font-weight:600;">Review Now</a>
        </p>
        """
        return subject, EmailService._wrap(subject, body)

    @staticmethod
    def approval_reminder_email(
        approver_name: str, employee_name: str, approval_url: str, reason: str
    ) -> tuple[str, str]:
        subject = f"Reminder: {employee_name}'s onboarding is still awaiting approval"
        body = f"""
        <p>Hi {approver_name},</p>
        <p>This is a reminder that <strong>{employee_name}</strong>'s onboarding approval is still pending.</p>
        <p><strong>Reason:</strong> {reason}</p>
        <p style="margin: 24px 0;">
          <a href="{approval_url}" style="background:#d97706;color:#fff;padding:12px 20px;
             border-radius:8px;text-decoration:none;font-weight:600;">Review Now</a>
        </p>
        """
        return subject, EmailService._wrap(subject, body)

    @staticmethod
    def onboarding_complete_email(employee_name: str, org_name: str) -> tuple[str, str]:
        subject = f"{employee_name} has completed onboarding"
        body = f"""
        <p>Good news - <strong>{employee_name}</strong> has finished onboarding at {org_name}
        and every provisioning task is healthy.</p>
        """
        return subject, EmailService._wrap(subject, body)
