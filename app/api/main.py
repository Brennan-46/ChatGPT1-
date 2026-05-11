import uuid

from fastapi import FastAPI, Request

from app.api.routes_agent import router as agent_router
from app.api.routes_health import router as health_router
from app.api.routes_metrics import router as metrics_router
from app.core.config import settings
from app.core.db import Base, engine
from app.metrics import incr
from app.observability_logging import configure_logging, log_event

configure_logging(settings.log_level)
Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.app_name)
app.include_router(health_router, prefix="/v1")
app.include_router(metrics_router, prefix="/v1")
app.include_router(agent_router, prefix="/v1")


@app.middleware('http')
async def correlation_middleware(request: Request, call_next):
    correlation_id = request.headers.get('x-correlation-id', str(uuid.uuid4()))
    request.state.correlation_id = correlation_id
    incr('http_requests_total')
    log_event('http_request', path=request.url.path, method=request.method, correlation_id=correlation_id)
    response = await call_next(request)
    if response.status_code >= 400:
        incr('http_failures_total')
    response.headers['x-correlation-id'] = correlation_id
    return response
