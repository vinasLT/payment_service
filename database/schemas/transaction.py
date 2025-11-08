from datetime import datetime

from pydantic import BaseModel, ConfigDict

from database.models.transaction import TransactionType


class TransactionBase(BaseModel):
    user_account_id: int
    plan_id: int | None = None
    transaction_type: TransactionType
    amount: int
    created_at: datetime | None = None
    updated_at: datetime | None = None


class TransactionCreate(TransactionBase):
    pass


class TransactionUpdate(BaseModel):
    plan_id: int | None = None
    transaction_type: TransactionType | None = None
    amount: int | None = None
    updated_at: datetime | None = None


class TransactionRead(TransactionBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
