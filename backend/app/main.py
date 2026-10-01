from contextlib import asynccontextmanager
import logging, os, time, uuid
from sqlalchemy import text
from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse, JSONResponse
from app.core.security import security_middleware
from app.core.rate_limit import rate_limit_middleware
from app.core.observability import metrics
from app.core.security import validate_security_configuration
from app.core.logging_config import configure_logging
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import CORS_ORIGINS
from app.api.transactions import router as transactions_router
from app.api.entities import router as entities_router
from app.api.context import router as context_router
from app.api.intelligence import router as intelligence_router
from app.api.dashboard import router as dashboard_router
from app.api.simulator import router as simulator_router
from app.api.websocket import router as websocket_router
from app.api.reconciliation import router as reconciliation_router
from app.api.investigations import router as investigations_router
from app.api.queries import router as queries_router
from app.api.partner_events import router as partner_events_router
from app.api.outcomes import router as outcomes_router
from app.api.graph import router as graph_router
from app.api.learning import router as learning_router
from app.websocket.manager import event_hub
from app.core.config import API_PREFIX
from app.db.database import engine
import app.models  # register models

@asynccontextmanager
async def lifespan(_: FastAPI):
    configure_logging()
    validate_security_configuration()
    event_hub.start()
    yield
    from app.simulator.event_generator import simulator
    simulator.stop()
    event_hub.stop()

app = FastAPI(title="Real-Time Financial Transaction Intelligence Platform", version="0.1.0", description="Synthetic/sandbox financial event foundation. No live UPI connectivity.", lifespan=lifespan)
app.middleware("http")(security_middleware)
app.middleware("http")(rate_limit_middleware)
app.add_middleware(CORSMiddleware,allow_origins=CORS_ORIGINS,allow_credentials=False,allow_methods=["GET","POST"],allow_headers=["Authorization","Content-Type"])
app.include_router(transactions_router, prefix=API_PREFIX)
app.include_router(entities_router, prefix=API_PREFIX)
app.include_router(context_router, prefix=API_PREFIX)
app.include_router(intelligence_router, prefix=API_PREFIX)
app.include_router(dashboard_router, prefix=API_PREFIX)
app.include_router(simulator_router, prefix=API_PREFIX)
app.include_router(reconciliation_router, prefix=API_PREFIX)
app.include_router(investigations_router, prefix=API_PREFIX)
app.include_router(queries_router, prefix=API_PREFIX)
app.include_router(partner_events_router, prefix=API_PREFIX)
app.include_router(outcomes_router, prefix=API_PREFIX)
app.include_router(graph_router, prefix=API_PREFIX)
app.include_router(learning_router, prefix=API_PREFIX)
app.include_router(websocket_router)

@app.middleware("http")
async def request_observability(request: Request, call_next):
    request_id=str(uuid.uuid4())
    started=time.perf_counter()
    response=await call_next(request)
    elapsed=time.perf_counter()-started
    route=getattr(request.scope.get("route"),"path",request.url.path)
    metrics.record(request.method,route,response.status_code,elapsed)
    response.headers["X-Request-ID"]=request_id
    logging.getLogger("finintel.request").info("request complete method=%s route=%s status=%d latency_ms=%.2f request_id=%s",request.method,route,response.status_code,elapsed*1000,request_id)
    return response

@app.get("/metrics",response_class=PlainTextResponse)
def get_metrics(): return metrics.prometheus()

@app.get("/readyz")
def readiness():
    try:
        with engine.connect() as connection: connection.execute(text("SELECT 1"))
        auth_required=os.getenv("AUTH_REQUIRED","false").lower()=="true"
        auth_ready=(not auth_required) or (len(os.getenv("API_KEY_ANALYST",""))>=32 and len(os.getenv("API_KEY_OPERATOR",""))>=32 and os.getenv("API_KEY_ANALYST")!=os.getenv("API_KEY_OPERATOR"))
        if not auth_ready: return JSONResponse({"status":"not_ready","database":"ready","auth":"missing or weak API keys"},status_code=503)
        return {"status":"ready","database":"ready","redis":"connected" if event_hub.redis else "local fallback","auth":"enabled" if os.getenv("AUTH_REQUIRED","false").lower()=="true" else "demo mode"}
    except Exception:
        return JSONResponse({"status":"not_ready","database":"unavailable"},status_code=503)

@app.get("/health")
def health():
    return {"status": "ok", "environment": "synthetic/sandbox"}
