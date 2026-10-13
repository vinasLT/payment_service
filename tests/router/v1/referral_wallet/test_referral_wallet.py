from __future__ import annotations

import sys
from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parent
if str(PACKAGE_DIR) not in sys.path:
    sys.path.insert(0, str(PACKAGE_DIR))

import _setup  # noqa: F401

from config import Permissions
from wallet_helpers import build_user, get_wallet, seed_wallet


def test_me_returns_zero_wallet_when_missing(api_client):
    client, user_context, _ = api_client
    user_context.user = build_user("user-1", [Permissions.REFERRAL_WALLET_OWN_READ.value])

    response = client.get("/private/v1/referral-wallet/me")

    assert response.status_code == 200
    assert response.json() == {
        "balance_cents": 0,
        "total_earned_cents": 0,
        "total_paid_out_cents": 0,
        "currency": "EUR",
    }


def test_my_transactions_are_paginated(api_client):
    client, user_context, session_factory = api_client
    user_context.user = build_user("user-1", [Permissions.REFERRAL_WALLET_OWN_READ.value])
    seed_wallet(session_factory, "user-1", 1000)

    response = client.get("/private/v1/referral-wallet/me/transactions")

    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 1
    assert body["data"][0]["amount_cents"] == 1000
    assert body["data"][0]["type"] == "reward_credit"


def test_admin_stats_and_user_wallet(api_client):
    client, user_context, session_factory = api_client
    seed_wallet(session_factory, "user-1", 1000)
    user_context.user = build_user("admin", [Permissions.REFERRAL_WALLET_ALL_READ.value])

    stats = client.get("/private/v1/referral-wallet/admin/stats")
    assert stats.status_code == 200
    assert stats.json()["total_wallet_balance_cents"] == 1000
    assert stats.json()["total_paid_out_cents"] == 0

    wallet = client.get("/private/v1/referral-wallet/admin/users/user-1")
    assert wallet.status_code == 200
    assert wallet.json()["balance_cents"] == 1000


def test_payout_and_adjustment(api_client):
    client, user_context, session_factory = api_client
    seed_wallet(session_factory, "user-1", 1000)
    user_context.user = build_user("admin", [Permissions.REFERRAL_WALLET_ALL_WRITE.value])

    payout = client.post("/private/v1/referral-wallet/admin/users/user-1/payouts", json={
        "amount_cents": 400,
        "external_reference": "bank-1",
    })
    assert payout.status_code == 201
    assert payout.json()["amount_cents"] == -400
    assert payout.json()["balance_after_cents"] == 600
    assert payout.json()["created_by_user_uuid"] == "admin"

    too_much = client.post("/private/v1/referral-wallet/admin/users/user-1/payouts", json={"amount_cents": 900})
    assert too_much.status_code == 400

    adjustment = client.post("/private/v1/referral-wallet/admin/users/user-1/adjustments", json={
        "amount_cents": -100,
        "note": "correction",
    })
    assert adjustment.status_code == 201
    assert adjustment.json()["balance_after_cents"] == 500
    assert get_wallet(session_factory, "user-1").balance_cents == 500
