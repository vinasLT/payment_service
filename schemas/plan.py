from pydantic import BaseModel

from core.utils import create_pagination_page
from database.schemas.plan import PlanRead


class PlanAssignPayload(BaseModel):
    user_uuid: str
    plan_id: int


PlansPage = create_pagination_page(PlanRead)
