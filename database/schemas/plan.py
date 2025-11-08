from datetime import datetime

from pydantic import BaseModel, ConfigDict


class PlanBase(BaseModel):
    name: str
    description: str | None = None
    max_bid_one_time: float
    bid_power: int
    price: float
    created_at: datetime | None = None
    updated_at: datetime | None = None


class PlanCreate(PlanBase):
    pass


class PlanUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    max_bid_one_time: float | None = None
    bid_power: int | None = None
    price: float | None = None
    updated_at: datetime | None = None


class PlanRead(PlanBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
