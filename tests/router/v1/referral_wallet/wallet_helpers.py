from __future__ import annotations

import sys
from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parent
if str(PACKAGE_DIR) not in sys.path:
    sys.path.insert(0, str(PACKAGE_DIR))

import _setup  # noqa: F401

from AuthTools import HeaderUser
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from database.models.referral_wallet import ReferralWallet
from database.models.referral_wallet_transaction import ReferralWalletTransaction, ReferralWalletTransactionType


def build_user(uuid: str, permissions: list[str]) -> HeaderUser:
    return HeaderUser(
        uuid=uuid,
        email="user@example.com",
        roles=["user"],
        token_expire="",
        permissions=permissions,
    )


def seed_wallet(session_factory: sessionmaker[Session], user_uuid: str, balance_cents: int) -> int:
    with session_factory() as session:
        wallet = ReferralWallet(
            user_uuid=user_uuid,
            balance_cents=balance_cents,
            total_earned_cents=balance_cents,
            total_paid_out_cents=0,
        )
        session.add(wallet)
        session.flush()
        session.add(ReferralWalletTransaction(
            wallet_id=wallet.id,
            type=ReferralWalletTransactionType.REWARD_CREDIT,
            amount_cents=balance_cents,
            balance_after_cents=balance_cents,
            reward_id=1,
        ))
        session.commit()
        return wallet.id


def get_wallet(session_factory: sessionmaker[Session], user_uuid: str) -> ReferralWallet | None:
    with session_factory() as session:
        return session.scalar(select(ReferralWallet).where(ReferralWallet.user_uuid == user_uuid))
