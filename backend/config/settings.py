from typing import List, Optional

from pydantic_settings import BaseSettings


def _is_placeholder(value: Optional[str]) -> bool:
    """A value counts as unset when it is empty or still carries a placeholder marker."""
    if not value:
        return True
    lowered = value.strip().lower()
    return lowered.startswith("placeholder") or lowered in {"changeme", "todo", "none", "null"}


class Settings(BaseSettings):
    app_name: str = "Echo Enterprise Autonomous Workforce"
    api_v1_str: str = "/api/v1"

    # ------------------------------------------------------------------
    # Environment
    # ------------------------------------------------------------------
    environment: str = "development"
    port: int = 8000
    log_level: str = "INFO"
    enable_structured_logging: bool = True

    # ------------------------------------------------------------------
    # Application URLs
    # ------------------------------------------------------------------
    app_url: str = "http://localhost:3000"
    frontend_url: str = "http://localhost:3000"
    backend_url: str = "http://localhost:8000"
    cors_origins: str = "*"

    # ------------------------------------------------------------------
    # Database / Supabase
    # ------------------------------------------------------------------
    database_url: str = "sqlite:///./echo.db"
    supabase_url: str = "placeholder_supabase_url"
    supabase_anon_key: str = "placeholder_supabase_anon_key"
    supabase_service_role_key: str = "placeholder_supabase_service_role_key"
    supabase_storage_bucket: str = "echo-documents"
    # Legacy alias kept for backwards compatibility with the original settings file.
    supabase_key: str = "placeholder_supabase_key"

    # ------------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------------
    jwt_secret: str = "echo-dev-jwt-secret-change-me"
    session_secret: str = "echo-dev-session-secret-change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24
    invitation_expiry_hours: int = 72

    # ------------------------------------------------------------------
    # LLM providers
    # ------------------------------------------------------------------
    llm_provider: str = "auto"  # auto | gemini | groq | openai | rules
    gemini_api_key: str = "placeholder_gemini_key"
    gemini_model: str = "gemini-2.0-flash"
    groq_api_key: str = "placeholder_groq_key"
    groq_model: str = "llama-3.3-70b-versatile"
    openai_api_key: str = "placeholder_openai_key"
    openai_model: str = "gpt-4o-mini"
    llm_timeout_seconds: int = 30

    # ------------------------------------------------------------------
    # Email (Gmail SMTP by default)
    # ------------------------------------------------------------------
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = "Echo WorkforceOS <no-reply@echo.local>"
    smtp_use_tls: bool = True

    # ------------------------------------------------------------------
    # Google Calendar
    # ------------------------------------------------------------------
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:8000/api/v1/integrations/google/callback"
    google_refresh_token: str = ""
    google_calendar_id: str = "primary"

    # ------------------------------------------------------------------
    # Slack / Jira
    # ------------------------------------------------------------------
    slack_bot_token: str = ""
    slack_default_channel: str = "#onboarding"
    jira_base_url: str = ""
    jira_user_email: str = ""
    jira_api_token: str = ""
    jira_project_key: str = "IT"

    # ------------------------------------------------------------------
    # AI Workflow & Escalation Policies
    # ------------------------------------------------------------------
    max_retries: int = 3
    retry_backoff_factor: float = 1.5
    escalation_timeout_seconds: int = 3600  # 1 hour
    approval_reminder_seconds: int = 900  # 15 minutes
    require_manager_approval: bool = True
    default_workflow_template: str = "employee_onboarding"

    # ------------------------------------------------------------------
    # Feature flags
    # ------------------------------------------------------------------
    enable_email: bool = False
    enable_realtime: bool = True
    enable_langgraph: bool = False
    enable_langfuse: bool = False
    enable_google_calendar: bool = False
    enable_slack: bool = False
    enable_jira: bool = False
    enable_seed: bool = True

    model_config = {
        "env_file": (".env", "../.env"),
        "env_file_encoding": "utf-8",
        "extra": "ignore"
    }

    # ------------------------------------------------------------------
    # Derived helpers
    # ------------------------------------------------------------------
    @property
    def is_development(self) -> bool:
        return self.environment.lower() in {"development", "dev", "local"}

    @property
    def supabase_secret_key(self) -> str:
        """Service role key, falling back to the legacy `supabase_key` field."""
        if not _is_placeholder(self.supabase_service_role_key):
            return self.supabase_service_role_key
        if not _is_placeholder(self.supabase_key):
            return self.supabase_key
        return ""

    @property
    def supabase_enabled(self) -> bool:
        """Supabase is only usable when we have a real project URL plus a key."""
        url = self.supabase_url or ""
        return url.startswith("http") and bool(self.supabase_secret_key)

    @property
    def gemini_enabled(self) -> bool:
        return not _is_placeholder(self.gemini_api_key)

    @property
    def groq_enabled(self) -> bool:
        return not _is_placeholder(self.groq_api_key)

    @property
    def openai_enabled(self) -> bool:
        return not _is_placeholder(self.openai_api_key)

    @property
    def smtp_enabled(self) -> bool:
        return self.enable_email and bool(self.smtp_user) and bool(self.smtp_password)

    @property
    def slack_enabled(self) -> bool:
        return self.enable_slack and bool(self.slack_bot_token)

    @property
    def jira_enabled(self) -> bool:
        return self.enable_jira and bool(self.jira_base_url) and bool(self.jira_api_token)

    @property
    def google_calendar_enabled(self) -> bool:
        return (
            self.enable_google_calendar
            and bool(self.google_client_id)
            and bool(self.google_client_secret)
            and bool(self.google_refresh_token)
        )

    @property
    def cors_origin_list(self) -> List[str]:
        if not self.cors_origins or self.cors_origins.strip() == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
