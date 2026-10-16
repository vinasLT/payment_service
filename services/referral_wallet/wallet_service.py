from typing import Optional

from fastapi_problem import error as problem
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from core.logger import logger
from database.crud.referral_wallet import ReferralWalletService
from database.crud.referral_wallet_transaction import ReferralWalletTransactionService
from database.models.referral_wallet import ReferralWallet
from database.models.referral_wallet_transaction import ReferralWalletTransaction, ReferralWalletTransactionType


class WalletService:
    """Every balance change locks the wallet row and writes a ledger entry in the same transaction."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.wallet_service = ReferralWalletService(session)
        self.transaction_service = ReferralWalletTransactionService(session)

    async def get_or_create_wallet(self, user_uuid: str, lock: bool = False) -> ReferralWallet:
        wallet = await self.wallet_service.get_by_user_uuid(user_uuid, for_update=lock)
        if wallet:
            return wallet
        wallet = ReferralWallet(user_uuid=user_uuid, balance_cents=0, total_earned_cents=0, total_paid_out_cents=0)
        self.session.add(wallet)
        try:
            await self.session.flush()
        except IntegrityError:
            await self.session.rollback()
            wallet = await self.wallet_service.get_by_user_uuid(user_uuid, for_update=lock)
            if wallet is None:
                raise
        return wallet

    async def credit_reward(
            self,
            referrer_uuid: str,
            reward_id: int,
            amount_cents: int,
            external_purchase_id: Optional[str] = None,
            admin_uuid: Optional[str] = None,
            note: Optional[str] = None,
    ) -> ReferralWallet:
        wallet = await self.get_or_create_wallet(referrer_uuid, lock=True)
        last = await self.transaction_service.get_last_reward_entry(reward_id)
        if last is not None and last.type == ReferralWalletTransactionType.REWARD_CREDIT:
            return wallet

        wallet.total_earned_cents += amount_cents
        self._add_transaction(
            wallet,
            amount_cents=amount_cents,
            transaction_type=ReferralWalletTransactionType.REWARD_CREDIT,
            reward_id=reward_id,
            admin_uuid=admin_uuid,
            note=note or f"Reward for purchase {external_purchase_id}",
        )
        await self.session.commit()
        await self.session.refresh(wallet)

        logger.info("Referral reward credited", extra={
            "reward_id": reward_id,
            "referrer_uuid": referrer_uuid,
            "amount_cents": amount_cents,
            "admin_uuid": admin_uuid,
        })
        return wallet

    async def reverse_reward(
            self,
            referrer_uuid: str,
            reward_id: int,
            amount_cents: int,
            external_purchase_id: Optional[str] = None,
            admin_uuid: Optional[str] = None,
            note: Optional[str] = None,
    ) -> Optional[ReferralWallet]:
        wallet = await self.wallet_service.get_by_user_uuid(referrer_uuid, for_update=True)
        if wallet is None:
            return None
        last = await self.transaction_service.get_last_reward_entry(reward_id)
        if last is None or last.type != ReferralWalletTransactionType.REWARD_CREDIT:
            return wallet

        wallet.total_earned_cents -= amount_cents
        self._add_transaction(
            wallet,
            amount_cents=-amount_cents,
            transaction_type=ReferralWalletTransactionType.REWARD_REVERSAL,
            reward_id=reward_id,
            admin_uuid=admin_uuid,
            note=note or f"Reversal of reward for purchase {external_purchase_id}",
        )
        await self.session.commit()
        await self.session.refresh(wallet)

        logger.info("Referral reward reversed", extra={
            "reward_id": reward_id,
            "referrer_uuid": referrer_uuid,
            "amount_cents": amount_cents,
            "admin_uuid": admin_uuid,
        })
        return wallet

    async def payout(
            self,
            user_uuid: str,
            amount_cents: int,
            admin_uuid: str,
            note: Optional[str] = None,
            external_reference: Optional[str] = None,
    ) -> ReferralWalletTransaction:
        wallet = await self.get_or_create_wallet(user_uuid, lock=True)
        if amount_cents > wallet.balance_cents:
            detail = f"Payout {amount_cents} exceeds wallet balance {wallet.balance_cents}"
            await self.session.rollback()
            raise problem.BadRequestProblem(detail=detail)

        wallet.total_paid_out_cents += amount_cents
        transaction = self._add_transaction(
            wallet,
            amount_cents=-amount_cents,
            transaction_type=ReferralWalletTransactionType.PAYOUT,
            admin_uuid=admin_uuid,
            note=note,
            external_reference=external_reference,
        )
        await self.session.commit()
        await self.session.refresh(transaction)

        logger.info("Referral wallet payout", extra={
            "user_uuid": user_uuid,
            "amount_cents": amount_cents,
            "admin_uuid": admin_uuid,
        })
        return transaction

    async def adjust(self, user_uuid: str, amount_cents: int, admin_uuid: str, note: str) -> ReferralWalletTransaction:
        wallet = await self.get_or_create_wallet(user_uuid, lock=True)
        if wallet.balance_cents + amount_cents < 0:
            detail = f"Adjustment {amount_cents} would make wallet balance negative ({wallet.balance_cents})"
            await self.session.rollback()
            raise problem.BadRequestProblem(detail=detail)

        transaction = self._add_transaction(
            wallet,
            amount_cents=amount_cents,
            transaction_type=ReferralWalletTransactionType.ADJUSTMENT,
            admin_uuid=admin_uuid,
            note=note,
        )
        await self.session.commit()
        await self.session.refresh(transaction)

        logger.info("Referral wallet adjustment", extra={
            "user_uuid": user_uuid,
            "amount_cents": amount_cents,
            "admin_uuid": admin_uuid,
        })
        return transaction

    def _add_transaction(
            self,
            wallet: ReferralWallet,
            amount_cents: int,
            transaction_type: ReferralWalletTransactionType,
            reward_id: Optional[int] = None,
            admin_uuid: Optional[str] = None,
            note: Optional[str] = None,
            external_reference: Optional[str] = None,
    ) -> ReferralWalletTransaction:
        wallet.balance_cents += amount_cents
        transaction = ReferralWalletTransaction(
            wallet_id=wallet.id,
            type=transaction_type,
            amount_cents=amount_cents,
            balance_after_cents=wallet.balance_cents,
            reward_id=reward_id,
            created_by_user_uuid=admin_uuid,
            note=note,
            external_reference=external_reference,
        )
        self.session.add(transaction)
        return transaction
