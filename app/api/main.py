from fastapi import FastAPI

from app.api.routes_agent import router as agent_router
from app.api.routes_health import router as health_router
from app.core.config import settings
from app.core.db import Base, engine
from app.observability_logging import configure_logging

configure_logging(settings.log_level)
Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.app_name)
app.include_router(health_router, prefix="/v1")
app.include_router(agent_router, prefix="/v1")
