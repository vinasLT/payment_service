from pydantic import BaseModel, ConfigDict


class UserAccountBase(BaseModel):
    user_uuid: str
    plan_id: int | None = None
    balance: int = 0


class UserAccountCreate(UserAccountBase):
    pass


class UserAccountUpdate(BaseModel):
    user_uuid: str | None = None
    plan_id: int | None = None
    balance: int | None = None


class UserAccountRead(UserAccountBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
