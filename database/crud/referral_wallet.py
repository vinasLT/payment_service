from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.crud.base import BaseService
from database.models.referral_wallet import ReferralWallet
from database.schemas.referral_wallet import ReferralWalletCreate, ReferralWalletUpdate


class ReferralWalletService(BaseService[ReferralWallet, ReferralWalletCreate, ReferralWalletUpdate]):
    def __init__(self, db: AsyncSession):
        super().__init__(ReferralWallet, db)

    async def get_by_user_uuid(self, user_uuid: str, for_update: bool = False) -> Optional[ReferralWallet]:
        stmt = select(ReferralWallet).where(ReferralWallet.user_uuid == user_uuid)
        if for_update:
            stmt = stmt.with_for_update().execution_options(populate_existing=True)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_totals(self) -> tuple[int, int]:
        stmt = select(
            func.coalesce(func.sum(ReferralWallet.balance_cents), 0),
            func.coalesce(func.sum(ReferralWallet.total_paid_out_cents), 0),
        )
        row = (await self.session.execute(stmt)).one()
        return int(row[0]), int(row[1])
