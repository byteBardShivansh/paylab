import json
import logging
from collections.abc import Generator
from app import payment_service
from datetime import datetime
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException, status
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import Settings, get_settings
from app.models import Base, PaymentCreate, PaymentRead


# ==================
# Structured Logging
# ==================
class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.utcnow().isoformat(timespec="milliseconds") + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        if hasattr(record, "extra") and isinstance(record.extra, dict):
            payload.update(record.extra)
        return json.dumps(payload, ensure_ascii=False)


def configure_logging(level: str = "INFO") -> None:
    root = logging.getLogger()
    root.setLevel(level.upper())
    # Clear existing handlers to avoid duplicate logs (esp. with uvicorn)
    for h in list(root.handlers):
        root.removeHandler(h)

    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    root.addHandler(handler)

    # Align uvicorn loggers
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        logger = logging.getLogger(name)
        logger.handlers = []
        logger.propagate = True
        logger.setLevel(level.upper())


# =============
# Database setup
# =============
def _create_engine(db_url: str):
    connect_args = {}
    if db_url.startswith("sqlite"):  # needed for SQLite file or memory
        connect_args = {"check_same_thread": False}
    return create_engine(db_url, future=True, pool_pre_ping=True, connect_args=connect_args)


settings = get_settings()
engine = _create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False, future=True)


# ======================
# Dependencies & Security
# ======================

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def verify_api_key(
    cfg: Annotated[Settings, Depends(get_settings)],
    x_api_key: Annotated[str | None, Header(alias="X-API-KEY")] = None,
) -> None:
    if not x_api_key or x_api_key != cfg.API_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing API key")


# =====
# App
# =====
app = FastAPI(title=settings.APP_NAME)


@app.on_event("startup")
def on_startup() -> None:
    cfg = get_settings()
    configure_logging(cfg.LOG_LEVEL)
    # Create tables if they do not exist. In production, prefer migrations.
    Base.metadata.create_all(bind=engine)
    logging.getLogger(__name__).info("service_started", extra={"extra": {"env": cfg.ENV}})


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/ready")
def ready(db: Annotated[Session, Depends(get_db)]):
    try:
        db.execute(select(1))
        return {"status": "ready"}
    except Exception as exc:  # pragma: no cover - exercised on misconfig
        logging.getLogger(__name__).exception("readiness_check_failed")
        raise HTTPException(status_code=503, detail="Database not ready") from exc


@app.post("/payments", response_model=PaymentRead, status_code=status.HTTP_201_CREATED, dependencies=[Depends(verify_api_key)])
def create_payment(payload: PaymentCreate, db: Annotated[Session, Depends(get_db)]):
    """
    Creates a new payment record.
    """
    return payment_service.create_new_payment(payload, db)