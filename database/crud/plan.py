from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.crud.base import BaseService
from database.models.plan import Plan
from database.schemas.plan import PlanCreate, PlanUpdate


class PlanService(BaseService[Plan, PlanCreate, PlanUpdate]):
    def __init__(self, db: AsyncSession):
        super().__init__(Plan, db)

    async def get_by_name(self, name: str) -> Plan | None:
        result = await self.session.execute(
            select(Plan).where(Plan.name == name)
        )
        return result.scalar_one_or_none()

    async def get_default_plan(self) -> Plan | None:
        stmt = select(Plan).order_by(Plan.id).limit(1)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
