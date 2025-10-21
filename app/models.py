"""
Database models and Pydantic DTOs for the payments service.
"""

from datetime import datetime
from decimal import Decimal
from typing import Literal, Protocol

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import DateTime, Integer, Numeric, String
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column


# =============
# Database setup
# =============
class Base(DeclarativeBase):
    pass


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
class PaymentRepositoryProtocol(Protocol):
    def create(self, data: PaymentCreate) -> Payment:
        """Creates a new payment record."""
        ...


class PaymentRepository:  # Implements PaymentRepositoryProtocol
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