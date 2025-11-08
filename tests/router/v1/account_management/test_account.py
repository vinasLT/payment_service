from __future__ import annotations

import sys
from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parent
if str(PACKAGE_DIR) not in sys.path:
    sys.path.insert(0, str(PACKAGE_DIR))

import _setup  # noqa: F401  # ensures env vars and sys.path are configured

from config import Permissions

from helpers import (
    build_user,
    count_transactions,
    get_account_by_uuid,
    get_latest_transaction,
    seed_account_with_plan,
)

from database.models.transaction import TransactionType


def test_get_my_account_creates_missing_account(api_client):
    client, user_context, session_factory = api_client
    requested_user = build_user(
        "user-me",
        [Permissions.ACCOUNT_OWN_READ.value],
    )
    user_context.user = requested_user

    response = client.get("/private/v1/account/me")
    assert response.status_code == 200

    payload = response.json()
    assert payload["user_uuid"] == requested_user.uuid
    assert payload["balance"] == 0
    assert payload["plan"] is None

    account = get_account_by_uuid(session_factory, requested_user.uuid)
    assert account is not None
    assert account.balance == 0
    assert account.plan_id is None


def test_reset_user_account_clears_balance_plan_and_transactions(api_client):
    client, user_context, session_factory = api_client
    target_user = "user-reset"

    account_id, bid_power = seed_account_with_plan(session_factory, target_user)

    user_context.user = build_user(
        "admin-user",
        [Permissions.ACCOUNT_ALL_WRITE.value],
    )

    response = client.post(
        "/private/v1/account/reset",
        json={"user_uuid": target_user},
    )
    assert response.status_code == 200

    payload = response.json()
    assert payload["user_uuid"] == target_user
    assert payload["balance"] == 0
    assert payload["plan"] is None

    account = get_account_by_uuid(session_factory, target_user)
    assert account is not None
    assert account.balance == 0
    assert account.plan_id is None

    txn_count = count_transactions(session_factory, account_id)
    assert txn_count == 2

    latest_txn = get_latest_transaction(session_factory, account_id)
    assert latest_txn is not None
    assert latest_txn.transaction_type == TransactionType.ADJUSTMENT
    assert latest_txn.amount == -bid_power
