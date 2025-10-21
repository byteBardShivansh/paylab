"""
Service layer for payment-related business logic.

This module encapsulates the logic for payment operations, separating it
from the HTTP transport layer (FastAPI routes).
"""

from sqlalchemy.orm import Session

from app.models import Payment, PaymentCreate, PaymentRepository, PaymentRead


def create_new_payment(payload: PaymentCreate, db: Session) -> PaymentRead:
    """
    Creates a new payment, saves it to the database, and returns the DTO.

    Args:
        payload: The payment creation data from the request.
        db: The database session dependency.

    Returns:
        A `PaymentRead` DTO for the newly created payment.
    """
    repo = PaymentRepository(db)
    payment = repo.create(payload)
    return PaymentRead.model_validate(payment)