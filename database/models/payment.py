from database.models import Base
from sqlalchemy import (
    Column, Integer, String, DateTime, Enum, Float, Index
)
from datetime import datetime, UTC

from database.schemas.payment import PaymentStatus


class Payment(Base):
    __tablename__ = "payment"

    id = Column(Integer, primary_key=True)
    user_external_id = Column(String, nullable=False, index=True)
    source = Column(String, nullable=False, index=True)
    provider = Column(String, nullable=False)

    amount = Column(Float, nullable=False)
    status = Column(Enum(PaymentStatus), nullable=False, default=PaymentStatus.PENDING)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    provider_payment_id = Column(String, nullable=True)

    purpose = Column(String, nullable=False)
    purpose_external_id = Column(Integer, nullable=False)

    __table_args__ = (
        Index('ix_user_source', 'user_external_id', 'source'),
        Index('ix_provider_payment_id', 'provider', 'provider_payment_id'),
    )



