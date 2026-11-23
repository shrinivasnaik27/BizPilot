"""BizPilot AI – FastAPI application entry point."""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import time

from .database import init_db
from .config import get_settings
from .utils.logger import get_logger
from .api.routes import auth, workflows, prospects, approvals, reports, business, marketing, agents

logger = get_logger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("BizPilot AI starting up …")
    init_db()
    logger.info(f"Demo mode: {settings.demo_mode} | DB: {settings.database_url[:30]}…")
    yield
    logger.info("BizPilot AI shutting down …")


app = FastAPI(
    title="BizPilot AI API",
    description="Intelligent Multi-Agent Business Automation Platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request timing
@app.middleware("http")
async def add_process_time(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    response.headers["X-Process-Time"] = f"{time.time() - start:.4f}s"
    return response


# Global error handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception on {request.url}: {exc}")
    return JSONResponse(
        status_code=500, content={"error": "Internal server error", "detail": str(exc)}
    )


# Routers
app.include_router(auth.router)
app.include_router(workflows.router)
app.include_router(prospects.router)
app.include_router(approvals.router)
app.include_router(reports.router)
app.include_router(business.router)
app.include_router(marketing.router)
app.include_router(agents.router)


@app.get("/", tags=["Root"])
async def root():
    return {
        "name": "BizPilot AI",
        "tagline": "One Instruction. Complete Business Execution.",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
async def health_check():
    from .database import engine
    from sqlalchemy import text

    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {e}"

    return {
        "status": "healthy",
        "database": db_status,
        "demo_mode": settings.demo_mode,
        "version": "1.0.0",
    }
