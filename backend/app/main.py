from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from app.core.config import get_settings
from app.db.session import Base, engine
from app.models import Certificate, GenerationJob  # noqa: F401
from app.api.jobs import router as jobs_router
from app.api.certificates import router as certificates_router

settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(title=settings.app_name, version="1.0.0", description="Bulk certificate generation API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(jobs_router, prefix="/api/v1")
app.include_router(certificates_router, prefix="/api/v1")

@app.get("/health")
def health():
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    return {"status": "ok", "service": settings.app_name}

@app.get("/")
def root():
    return {"service": settings.app_name, "docs": "/docs", "health": "/health"}
