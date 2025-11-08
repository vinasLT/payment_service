from pydantic import BaseModel, ConfigDict

from database.schemas.plan import PlanRead
from database.schemas.user_account import UserAccountRead


class UserAccountDetailed(UserAccountRead):
    plan: PlanRead | None

    model_config = ConfigDict(from_attributes=True)


class AccountResetPayload(BaseModel):
    user_uuid: str
