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
    create_plan_record,
    get_account_by_uuid,
    plan_exists,
)


def test_list_plans_returns_paginated_result(api_client):
    client, user_context, session_factory = api_client
    user_context.user = build_user(
        "plan-reader",
        [Permissions.PLAN_ALL_READ.value],
    )
    create_plan_record(session_factory, name="ListPlan", bid_power=10)

    response = client.get("/private/v1/plan")
    assert response.status_code == 200

    payload = response.json()
    assert "data" in payload and isinstance(payload["data"], list)
    assert payload["count"] >= 1
    assert any(plan["name"] == "ListPlan" for plan in payload["data"])


def test_create_plan_returns_created_plan(api_client):
    client, user_context, _ = api_client
    user_context.user = build_user(
        "plan-writer",
        [Permissions.PLAN_ALL_WRITE.value],
    )
    plan_payload = {
        "name": "CreatePlan",
        "description": "create desc",
        "max_bid_one_time": 20.0,
        "bid_power": 30,
        "price": 99.0,
    }

    response = client.post("/private/v1/plan", json=plan_payload)
    assert response.status_code == 201

    payload = response.json()
    for key, value in plan_payload.items():
        assert payload[key] == value


def test_get_plan_returns_plan_details(api_client):
    client, user_context, session_factory = api_client
    plan = create_plan_record(session_factory, name="FetchPlan", bid_power=60)
    user_context.user = build_user(
        "plan-reader",
        [Permissions.PLAN_ALL_READ.value],
    )

    response = client.get(f"/private/v1/plan/{plan.id}")
    assert response.status_code == 200

    payload = response.json()
    assert payload["id"] == plan.id
    assert payload["name"] == "FetchPlan"


def test_update_plan_modifies_fields(api_client):
    client, user_context, session_factory = api_client
    plan = create_plan_record(session_factory, name="UpdatePlan", price=50.0)
    user_context.user = build_user(
        "plan-writer",
        [Permissions.PLAN_ALL_WRITE.value],
    )

    response = client.put(
        f"/private/v1/plan/{plan.id}",
        json={"price": 150.0, "description": "updated"},
    )
    assert response.status_code == 200

    payload = response.json()
    assert payload["price"] == 150.0
    assert payload["description"] == "updated"


def test_delete_plan_removes_plan(api_client):
    client, user_context, session_factory = api_client
    plan = create_plan_record(session_factory, name="DeletePlan")
    user_context.user = build_user(
        "plan-admin",
        [Permissions.PLAN_ALL_DELETE.value],
    )

    response = client.delete(f"/private/v1/plan/{plan.id}")
    assert response.status_code == 204

    exists = plan_exists(session_factory, plan.id)
    assert exists is False


def test_assign_plan_to_account_updates_balance_and_transactions(api_client):
    client, user_context, session_factory = api_client
    plan = create_plan_record(session_factory, name="AssignPlan", bid_power=80)
    target_user = "user-plan-assign"
    user_context.user = build_user(
        "plan-writer",
        [
            Permissions.PLAN_ALL_WRITE.value,
            Permissions.ACCOUNT_ALL_WRITE.value,
        ],
    )

    response = client.post(
        "/private/v1/plan/assign",
        json={"user_uuid": target_user, "plan_id": plan.id},
    )
    assert response.status_code == 200

    payload = response.json()
    assert payload["user_uuid"] == target_user
    assert payload["balance"] == plan.bid_power
    assert payload["plan"]["id"] == plan.id

    account = get_account_by_uuid(session_factory, target_user)
    assert account.plan_id == plan.id

    txn_count = count_transactions(session_factory, account.id)
    assert txn_count == 1
