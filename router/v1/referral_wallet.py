from AuthTools import HeaderUser
from AuthTools.Permissions.dependencies import require_permissions
from fastapi import APIRouter, Body, Depends, Path
from fastapi_pagination.ext.sqlalchemy import apaginate
from sqlalchemy.ext.asyncio import AsyncSession

from config import Permissions, settings
from database.crud.referral_wallet import ReferralWalletService
from database.crud.referral_wallet_transaction import ReferralWalletTransactionService
from database.db.session import get_db
from schemas.referral_wallet import (
    AdjustmentPayload,
    AdminReferralWalletStatsOut,
    AdminReferralWalletTransactionOut,
    AdminReferralWalletTransactionPage,
    PayoutPayload,
    ReferralWalletTransactionPage,
    WalletOut,
)
from services.referral_wallet.wallet_service import WalletService

referral_wallet_router = APIRouter(prefix="/referral-wallet", tags=["Referral Wallet"])


def _wallet_out(wallet) -> WalletOut:
    return WalletOut(
        balance_cents=wallet.balance_cents if wallet else 0,
        total_earned_cents=wallet.total_earned_cents if wallet else 0,
        total_paid_out_cents=wallet.total_paid_out_cents if wallet else 0,
        currency=settings.REFERRAL_CURRENCY,
    )


@referral_wallet_router.get("/me", response_model=WalletOut, description="Referral wallet of the current user")
async def get_my_wallet(
        current_user: HeaderUser = Depends(require_permissions(Permissions.REFERRAL_WALLET_OWN_READ)),
        db: AsyncSession = Depends(get_db),
) -> WalletOut:
    wallet = await ReferralWalletService(db).get_by_user_uuid(current_user.uuid)
    return _wallet_out(wallet)


@referral_wallet_router.get("/me/transactions", response_model=ReferralWalletTransactionPage,
                            description="Referral wallet history of the current user")
async def get_my_transactions(
        current_user: HeaderUser = Depends(require_permissions(Permissions.REFERRAL_WALLET_OWN_READ)),
        db: AsyncSession = Depends(get_db),
):
    stmt = ReferralWalletTransactionService(db).get_user_transactions_stmt(current_user.uuid)
    return await apaginate(db, stmt)


@referral_wallet_router.get("/admin/stats", response_model=AdminReferralWalletStatsOut,
                            description="Total referral wallet balance and payouts",
                            dependencies=[Depends(require_permissions(Permissions.REFERRAL_WALLET_ALL_READ))])
async def get_admin_stats(db: AsyncSession = Depends(get_db)) -> AdminReferralWalletStatsOut:
    balance_cents, paid_out_cents = await ReferralWalletService(db).get_totals()
    return AdminReferralWalletStatsOut(
        total_wallet_balance_cents=balance_cents,
        total_paid_out_cents=paid_out_cents,
        currency=settings.REFERRAL_CURRENCY,
    )


@referral_wallet_router.get("/admin/users/{user_uuid}", response_model=WalletOut,
                            description="Referral wallet of a user",
                            dependencies=[Depends(require_permissions(Permissions.REFERRAL_WALLET_ALL_READ))])
async def get_admin_user_wallet(user_uuid: str = Path(...), db: AsyncSession = Depends(get_db)) -> WalletOut:
    wallet = await ReferralWalletService(db).get_by_user_uuid(user_uuid)
    return _wallet_out(wallet)


@referral_wallet_router.get("/admin/users/{user_uuid}/transactions", response_model=AdminReferralWalletTransactionPage,
                            description="Referral wallet history of a user",
                            dependencies=[Depends(require_permissions(Permissions.REFERRAL_WALLET_ALL_READ))])
async def get_admin_user_transactions(user_uuid: str = Path(...), db: AsyncSession = Depends(get_db)):
    stmt = ReferralWalletTransactionService(db).get_user_transactions_stmt(user_uuid)
    return await apaginate(db, stmt)


@referral_wallet_router.post("/admin/users/{user_uuid}/payouts", response_model=AdminReferralWalletTransactionOut,
                             status_code=201, description="Register a manual payout and deduct it from the wallet")
async def create_payout(
        user_uuid: str = Path(...),
        data: PayoutPayload = Body(...),
        admin: HeaderUser = Depends(require_permissions(Permissions.REFERRAL_WALLET_ALL_WRITE)),
        db: AsyncSession = Depends(get_db),
):
    return await WalletService(db).payout(
        user_uuid=user_uuid,
        amount_cents=data.amount_cents,
        admin_uuid=admin.uuid,
        note=data.note,
        external_reference=data.external_reference,
    )


@referral_wallet_router.post("/admin/users/{user_uuid}/adjustments", response_model=AdminReferralWalletTransactionOut,
                             status_code=201, description="Manual wallet correction (positive or negative)")
async def create_adjustment(
        user_uuid: str = Path(...),
        data: AdjustmentPayload = Body(...),
        admin: HeaderUser = Depends(require_permissions(Permissions.REFERRAL_WALLET_ALL_WRITE)),
        db: AsyncSession = Depends(get_db),
):
    return await WalletService(db).adjust(
        user_uuid=user_uuid,
        amount_cents=data.amount_cents,
        admin_uuid=admin.uuid,
        note=data.note,
    )
