from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from database.models.referral_wallet_transaction import ReferralWalletTransactionType


class ReferralWalletCreate(BaseModel):
    user_uuid: str


class ReferralWalletUpdate(BaseModel):
    balance_cents: Optional[int] = None
    total_earned_cents: Optional[int] = None
    total_paid_out_cents: Optional[int] = None


class ReferralWalletRead(BaseModel):
    id: int
    user_uuid: str
    balance_cents: int
    total_earned_cents: int
    total_paid_out_cents: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ReferralWalletTransactionCreate(BaseModel):
    wallet_id: int
    type: ReferralWalletTransactionType
    amount_cents: int
    balance_after_cents: int
    reward_id: Optional[int] = None
    created_by_user_uuid: Optional[str] = None
    external_reference: Optional[str] = None
    note: Optional[str] = None


class ReferralWalletTransactionUpdate(BaseModel):
    note: Optional[str] = None


class ReferralWalletTransactionRead(BaseModel):
    id: int
    type: ReferralWalletTransactionType
    amount_cents: int
    balance_after_cents: int
    reward_id: Optional[int]
    external_reference: Optional[str]
    note: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
