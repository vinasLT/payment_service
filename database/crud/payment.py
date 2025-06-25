from sqlalchemy import select

from database.crud.base import BaseService
from database.models.payment import Payment
from database.schemas.payment import PaymentCreate, PaymentUpdate


class PaymentService(BaseService[Payment, PaymentCreate, PaymentUpdate]):
    def __init__(self):
        super().__init__(Payment)

    async def __aenter__(self):
        await super().__aenter__()
        return self

    async def get_by_provider_payment_id(self, provider_payment_id: str) -> Payment:
        result = await self.session.execute(
            select(Payment).where(
                Payment.provider_payment_id == provider_payment_id,

            )
        )
        return result.scalar_one_or_none()


