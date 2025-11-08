from __future__ import annotations

from typing import Tuple

import sys
from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parent
if str(PACKAGE_DIR) not in sys.path:
    sys.path.insert(0, str(PACKAGE_DIR))

import _setup  # noqa: F401  # ensures env vars and sys.path are configured

from AuthTools import HeaderUser
from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker

from database.models.plan import Plan
from database.models.transaction import Transaction, TransactionType
from database.models.user_account import UserAccount


def build_user(uuid: str, permissions: list[str]) -> HeaderUser:
    return HeaderUser(
        uuid=uuid,
        email="user@example.com",
        roles=["user"],
        token_expire="",
        permissions=permissions,
    )


def get_account_by_uuid(
    session_factory: sessionmaker[Session], user_uuid: str
) -> UserAccount | None:
    with session_factory() as session:
        result = session.execute(
            select(UserAccount).where(UserAccount.user_uuid == user_uuid)
        )
        return result.scalar_one_or_none()


def count_transactions(
    session_factory: sessionmaker[Session], account_id: int
) -> int:
    with session_factory() as session:
        result = session.execute(
            select(func.count())
            .select_from(Transaction)
            .where(Transaction.user_account_id == account_id)
        )
        return int(result.scalar_one())


def get_latest_transaction(
    session_factory: sessionmaker[Session], account_id: int
) -> Transaction | None:
    with session_factory() as session:
        result = session.execute(
            select(Transaction)
            .where(Transaction.user_account_id == account_id)
            .order_by(Transaction.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()


def seed_account_with_plan(
    session_factory: sessionmaker[Session], user_uuid: str
) -> Tuple[int, int]:
    with session_factory() as session:
        plan = Plan(
            name="Pro",
            description="Test plan",
            max_bid_one_time=10.0,
            bid_power=50,
            price=25.0,
        )
        session.add(plan)
        session.flush()

        account = UserAccount(
            user_uuid=user_uuid,
            plan_id=plan.id,
            balance=plan.bid_power,
        )
        session.add(account)
        session.flush()

        transaction = Transaction(
            user_account_id=account.id,
            plan_id=plan.id,
            transaction_type=TransactionType.PLAN_PURCHASE,
            amount=plan.bid_power,
        )
        session.add(transaction)
        session.commit()

        return account.id, plan.bid_power


def create_plan_record(
    session_factory: sessionmaker[Session],
    *,
    name: str = "Plan",
    description: str = "Test plan",
    max_bid_one_time: float = 10.0,
    bid_power: int = 25,
    price: float = 15.0,
) -> Plan:
    with session_factory() as session:
        plan = Plan(
            name=name,
            description=description,
            max_bid_one_time=max_bid_one_time,
            bid_power=bid_power,
            price=price,
        )
        session.add(plan)
        session.commit()
        session.refresh(plan)
        return plan


def plan_exists(
    session_factory: sessionmaker[Session], plan_id: int
) -> bool:
    with session_factory() as session:
        result = session.execute(select(Plan).where(Plan.id == plan_id))
        return result.scalar_one_or_none() is not None


__all__ = [
    "build_user",
    "get_account_by_uuid",
    "count_transactions",
    "get_latest_transaction",
    "seed_account_with_plan",
    "create_plan_record",
    "plan_exists",
]
