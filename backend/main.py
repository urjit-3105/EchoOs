"""ECHO WorkforceOS - FastAPI application entrypoint.

Run from the ``backend`` directory:

    uvicorn main:app --reload --port 8000
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config.settings import settings
from core.logger.structured import get_logger
from database import get_database, init_database

# Importing the agents package registers every agent with the AgentRegistry.
import core.agents  # noqa: F401
# Importing the plugins package registers every tool with the ToolRegistry.
import core.execution.plugins  # noqa: F401

from routes import (
    agents,
    approvals,
    audit,
    auth,
    documents,
    employees,
    execution,
    health,
    integrations,
    invitations,
    monitoring,
    notifications,
    orchestrator,
    organizations,
    planner,
    portal,
    settings as settings_routes,
    tasks,
    verification,
    workflow,
)

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Prepare persistence, workflow templates and background schedulers."""
    await init_database()

    from core.workflow.templates import WorkflowTemplateRegistry
    from services.bootstrap import BootstrapService
    from services.onboarding import OnboardingService
    from services.scheduler import BackgroundScheduler

    await BootstrapService.initialize()
    WorkflowTemplateRegistry.load_all()
    await OnboardingService.register_event_handlers()
    await BackgroundScheduler.start()

    logger.info(
        "ECHO WorkforceOS started",
        context={
            "environment": settings.environment,
            "persistence": get_database().name,
            "templates": WorkflowTemplateRegistry.keys(),
        },
    )
    try:
        yield
    finally:
        await BackgroundScheduler.stop()
        logger.info("ECHO WorkforceOS shutting down")


app = FastAPI(
    title=settings.app_name,
    description="Enterprise Autonomous Workforce Operating System",
    version="1.0.0",
    openapi_url=f"{settings.api_v1_str}/openapi.json",
    lifespan=lifespan,
)

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(ValueError)
async def value_error_handler(_request, exc: ValueError):
    """Domain errors raised by services surface as 400s rather than 500s."""
    return JSONResponse(status_code=400, content={"detail": str(exc)})


# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(health.router)

for router in (
    auth.router,
    organizations.router,
    employees.router,
    invitations.router,
    documents.router,
    workflow.router,
    agents.router,
    notifications.router,
    tasks.router,
    approvals.router,
    audit.router,
    monitoring.router,
    integrations.router,
    settings_routes.router,
    portal.router,
    planner.router,
    orchestrator.router,
    verification.router,
    execution.router,
):
    app.include_router(router, prefix=settings.api_v1_str)


@app.get("/")
def root():
    return {
        "message": "Welcome to Echo API",
        "name": settings.app_name,
        "version": "1.0.0",
        "docs": "/docs",
        "api": settings.api_v1_str,
    }
