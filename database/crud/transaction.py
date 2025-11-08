from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.crud.base import BaseService
from database.models.transaction import Transaction
from database.schemas.transaction import TransactionCreate, TransactionUpdate


class TransactionService(
    BaseService[Transaction, TransactionCreate, TransactionUpdate]
):
    def __init__(self, db: AsyncSession):
        super().__init__(Transaction, db)

    async def list_by_user_account(self, user_account_id: int) -> list[Transaction]:
        result = await self.session.execute(
            select(Transaction)
            .where(Transaction.user_account_id == user_account_id)
            .order_by(Transaction.created_at.desc())
        )
        return list(result.scalars().all())
