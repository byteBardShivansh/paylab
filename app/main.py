import json
import logging
from datetime import datetime
from decimal import Decimal
from functools import lru_cache
from typing import Annotated, Literal

from fastapi import Depends, FastAPI, Header, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import DateTime, Integer, Numeric, String, create_engine, select
from sqlalchemy.orm import Mapped, Session, declarative_base, mapped_column, sessionmaker


# =========================
# Configuration (12-factor)
# =========================
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    APP_NAME: str = "payments-service"
    ENV: str = Field(default="development", description="Environment name: development/staging/production")
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")

    API_KEY: str = Field(default="dev-secret", description="API key required in X-API-KEY header")

    # Default to local SQLite file for quick start; override with Postgres in production
    DATABASE_URL: str = Field(
        default="sqlite+pysqlite:///./payments.db",
        description="SQLAlchemy DB URL. e.g., postgresql+psycopg://user:pass@host:5432/dbname",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]


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
Base = declarative_base()


def _create_engine(db_url: str):
    connect_args = {}
    if db_url.startswith("sqlite"):  # needed for SQLite file or memory
        connect_args = {"check_same_thread": False}
    return create_engine(db_url, future=True, pool_pre_ping=True, connect_args=connect_args)


settings = get_settings()
engine = _create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False, future=True)


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    order_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)


# =============
# Pydantic DTOs
# =============
class PaymentCreate(BaseModel):
    order_id: str = Field(min_length=1, max_length=64)
    amount: float = Field(gt=0, description="Payment amount, must be > 0")
    currency: Literal["USD"] = "USD"


class PaymentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    order_id: str
    amount: float
    currency: str
    created_at: datetime


# ==============
# Repositories
# ==============
class PaymentRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, data: PaymentCreate) -> Payment:
        # Store amount as Decimal with 2 places to align with schema
        amt = Decimal(str(round(data.amount, 2)))
        obj = Payment(order_id=data.order_id, amount=amt, currency=data.currency)
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj


# ======================
# Dependencies & Security
# ======================

def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def verify_api_key(
    x_api_key: Annotated[str | None, Header(alias="X-API-KEY")] = None,
    cfg: Annotated[Settings, Depends(get_settings)],
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
    repo = PaymentRepository(db)
    payment = repo.create(payload)
    # Convert Decimal to float for response serialization
    return PaymentRead(
        id=payment.id,
        order_id=payment.order_id,
        amount=float(payment.amount),
        currency=payment.currency,
        created_at=payment.created_at,
    )
