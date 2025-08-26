from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.crud.base import BaseService
from database.models.payment import Payment
from database.schemas.payment import PaymentCreate, PaymentUpdate


class PaymentService(BaseService[Payment, PaymentCreate, PaymentUpdate]):
    def __init__(self, db: AsyncSession):
        super().__init__(Payment, db)

    async def get_by_provider_payment_id(self, provider_payment_id: str) -> Payment:
        result = await self.session.execute(
            select(Payment).where(
                Payment.provider_payment_id == provider_payment_id,

            )
        )
        return result.scalar_one_or_none()


