from typing import Optional

from sqlalchemy import select, Select
from sqlalchemy.ext.asyncio import AsyncSession

from database.crud.base import BaseService
from database.models.referral_wallet import ReferralWallet
from database.models.referral_wallet_transaction import ReferralWalletTransaction, ReferralWalletTransactionType
from database.schemas.referral_wallet import ReferralWalletTransactionCreate, ReferralWalletTransactionUpdate


class ReferralWalletTransactionService(
    BaseService[ReferralWalletTransaction, ReferralWalletTransactionCreate, ReferralWalletTransactionUpdate]
):
    def __init__(self, db: AsyncSession):
        super().__init__(ReferralWalletTransaction, db)

    def get_user_transactions_stmt(self, user_uuid: str) -> Select[tuple[ReferralWalletTransaction]]:
        return (
            select(ReferralWalletTransaction)
            .join(ReferralWallet, ReferralWallet.id == ReferralWalletTransaction.wallet_id)
            .where(ReferralWallet.user_uuid == user_uuid)
            .order_by(ReferralWalletTransaction.created_at.desc(), ReferralWalletTransaction.id.desc())
        )

    async def get_last_reward_entry(self, reward_id: int) -> Optional[ReferralWalletTransaction]:
        stmt = (
            select(ReferralWalletTransaction)
            .where(
                ReferralWalletTransaction.reward_id == reward_id,
                ReferralWalletTransaction.type.in_([
                    ReferralWalletTransactionType.REWARD_CREDIT,
                    ReferralWalletTransactionType.REWARD_REVERSAL,
                ]),
            )
            .order_by(ReferralWalletTransaction.id.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
