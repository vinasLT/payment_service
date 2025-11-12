from __future__ import annotations

from typing import AsyncGenerator, Generator, Tuple

import sys
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from fastapi_pagination import add_pagination
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

PACKAGE_DIR = Path(__file__).resolve().parent
if str(PACKAGE_DIR) not in sys.path:
    sys.path.insert(0, str(PACKAGE_DIR))

import _setup  # noqa: F401  # ensure env vars and sys.path are configured

from AuthTools.Permissions.dependencies import get_user as auth_get_user

from config import Permissions
from database.db.session import get_db
from database.models import Base
from router.v1.account_management.account import account_management_router
from router.v1.account_management.plan import plan_management_router
from router.v1.account_management.plan_public import plan_public_router

from helpers import build_user


def _prepare_database(engine) -> None:
    Base.metadata.create_all(bind=engine)


def _dispose_database(engine) -> None:
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


class FakeAsyncSession:
    def __init__(self, sync_session: Session):
        self._session = sync_session

    async def execute(self, *args, **kwargs):
        return self._session.execute(*args, **kwargs)

    async def scalar(self, *args, **kwargs):
        return self._session.scalar(*args, **kwargs)

    def add(self, obj):
        self._session.add(obj)

    async def commit(self):
        self._session.commit()

    async def refresh(self, obj):
        self._session.refresh(obj)

    async def get(self, model, obj_id):
        return self._session.get(model, obj_id)

    async def delete(self, obj):
        self._session.delete(obj)

    async def close(self):
        self._session.close()

    async def flush(self):
        self._session.flush()


def _create_app() -> FastAPI:
    test_app = FastAPI()
    test_app.include_router(account_management_router, prefix="/private/v1")
    test_app.include_router(plan_management_router, prefix="/private/v1")
    test_app.include_router(plan_public_router, prefix="/public/v1")
    add_pagination(test_app)
    return test_app


@pytest.fixture
def api_client() -> Generator[Tuple[TestClient, object, sessionmaker], None, None]:
    app = _create_app()
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    _prepare_database(engine)
    TestingSessionLocal = sessionmaker(
        bind=engine,
        expire_on_commit=False,
        class_=Session,
    )

    async def override_get_db() -> AsyncGenerator:
        sync_session = TestingSessionLocal()
        fake_session = FakeAsyncSession(sync_session)
        try:
            yield fake_session
        finally:
            await fake_session.close()

    app.dependency_overrides[get_db] = override_get_db

    class UserContext:
        def __init__(self):
            self.user = build_user(
                "default-user",
                [
                    Permissions.ACCOUNT_OWN_READ.value,
                    Permissions.ACCOUNT_ALL_WRITE.value,
                ],
            )

    user_context = UserContext()

    def override_get_user():
        return user_context.user

    app.dependency_overrides[auth_get_user] = override_get_user

    with TestClient(app) as client:
        yield client, user_context, TestingSessionLocal

    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(auth_get_user, None)
    _dispose_database(engine)
