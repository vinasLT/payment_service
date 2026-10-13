from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from core.utils import create_pagination_page
from database.schemas.referral_wallet import ReferralWalletTransactionRead


class WalletOut(BaseModel):
    balance_cents: int = 0
    total_earned_cents: int = 0
    total_paid_out_cents: int = 0
    currency: str


class AdminReferralWalletStatsOut(BaseModel):
    total_wallet_balance_cents: int = 0
    total_paid_out_cents: int = 0
    currency: str


class ReferralWalletTransactionOut(ReferralWalletTransactionRead):
    pass


class AdminReferralWalletTransactionOut(ReferralWalletTransactionRead):
    created_by_user_uuid: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class PayoutPayload(BaseModel):
    amount_cents: int = Field(..., gt=0, description="Amount paid to the user, in cents")
    note: Optional[str] = Field(None, max_length=1000)
    external_reference: Optional[str] = Field(None, max_length=255, description="Bank transfer id or similar")


class AdjustmentPayload(BaseModel):
    amount_cents: int = Field(..., description="Positive to credit, negative to debit, in cents")
    note: str = Field(..., min_length=1, max_length=1000)

    @field_validator("amount_cents")
    @classmethod
    def non_zero(cls, v: int) -> int:
        if v == 0:
            raise ValueError("amount_cents must not be zero")
        return v


ReferralWalletTransactionPage = create_pagination_page(ReferralWalletTransactionOut)
AdminReferralWalletTransactionPage = create_pagination_page(AdminReferralWalletTransactionOut)
