import asyncio

import pytest
from fastapi_problem import error as problem
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from database.models import Base
from database.models.referral_wallet_transaction import ReferralWalletTransactionType
from services.referral_wallet.wallet_service import WalletService


def _run(coro):
    return asyncio.run(coro)


async def _session_factory():
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    return engine, async_sessionmaker(engine, expire_on_commit=False)


def test_credit_is_idempotent_until_reversed():
    async def body():
        engine, factory = await _session_factory()
        try:
            async with factory() as session:
                service = WalletService(session)
                wallet = await service.credit_reward("user-1", reward_id=7, amount_cents=1000,
                                                     external_purchase_id="p-1")
                assert wallet.balance_cents == 1000
                assert wallet.total_earned_cents == 1000

                wallet = await service.credit_reward("user-1", reward_id=7, amount_cents=1000,
                                                     external_purchase_id="p-1")
                assert wallet.balance_cents == 1000

                wallet = await service.reverse_reward("user-1", reward_id=7, amount_cents=1000,
                                                      external_purchase_id="p-1")
                assert wallet.balance_cents == 0
                assert wallet.total_earned_cents == 0

                skipped = await service.reverse_reward("user-1", reward_id=7, amount_cents=1000,
                                                       external_purchase_id="p-1")
                assert skipped.balance_cents == 0

                wallet = await service.credit_reward("user-1", reward_id=7, amount_cents=1000,
                                                     external_purchase_id="p-1")
                assert wallet.balance_cents == 1000
                assert wallet.total_earned_cents == 1000
        finally:
            await engine.dispose()

    _run(body())


def test_reverse_without_credit_does_nothing():
    async def body():
        engine, factory = await _session_factory()
        try:
            async with factory() as session:
                wallet = await WalletService(session).reverse_reward("user-2", reward_id=1, amount_cents=500)
                assert wallet is None
        finally:
            await engine.dispose()

    _run(body())


def test_payout_over_balance_is_rejected_and_adjust_changes_balance():
    async def body():
        engine, factory = await _session_factory()
        try:
            async with factory() as session:
                service = WalletService(session)
                await service.credit_reward("user-3", reward_id=3, amount_cents=1000, external_purchase_id="p-3")

                with pytest.raises(problem.BadRequestProblem):
                    await service.payout("user-3", amount_cents=1500, admin_uuid="admin")

                payout = await service.payout("user-3", amount_cents=400, admin_uuid="admin",
                                              external_reference="bank-1")
                assert payout.type == ReferralWalletTransactionType.PAYOUT
                assert payout.amount_cents == -400
                assert payout.balance_after_cents == 600

                adjustment = await service.adjust("user-3", amount_cents=-100, admin_uuid="admin", note="fix")
                assert adjustment.type == ReferralWalletTransactionType.ADJUSTMENT
                assert adjustment.balance_after_cents == 500

                with pytest.raises(problem.BadRequestProblem):
                    await service.adjust("user-3", amount_cents=-600, admin_uuid="admin", note="too much")
        finally:
            await engine.dispose()

    _run(body())
