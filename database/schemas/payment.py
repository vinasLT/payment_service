from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel


class PaymentStatus(str, Enum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class Purposes(str, Enum):
    CARFAX = "CARFAX"

class PaymentBase(BaseModel):
    user_external_id: str
    source: str
    provider: str
    amount: float
    status: PaymentStatus = PaymentStatus.PENDING
    purpose: Purposes
    purpose_external_id: str = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    provider_payment_id: Optional[str] = None

class PaymentCreate(PaymentBase):
    pass

class PaymentUpdate(BaseModel):
    user_external_id: Optional[str] = None
    source: Optional[str] = None
    provider: Optional[str] = None
    purpose: Purposes = None
    purpose_external_id: Optional[str] = None
    amount: Optional[float] = None
    status: Optional[PaymentStatus] = None
    provider_payment_id: Optional[str] = None
    updated_at: Optional[datetime] = None

class PaymentRead(PaymentBase):
    id: int

    class Config:
        from_attributes = True