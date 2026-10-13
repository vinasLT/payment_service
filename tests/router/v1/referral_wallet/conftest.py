from __future__ import annotations

import sys
from pathlib import Path
from typing import AsyncGenerator, Generator, Tuple

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from fastapi_pagination import add_pagination
from fastapi_problem.handler import add_exception_handler, new_exception_handler
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

PACKAGE_DIR = Path(__file__).resolve().parent
if str(PACKAGE_DIR) not in sys.path:
    sys.path.insert(0, str(PACKAGE_DIR))

import _setup  # noqa: F401

from AuthTools.Permissions.dependencies import get_user as auth_get_user

from config import Permissions
from database.db.session import get_db
from database.models import Base
from router.v1.referral_wallet import referral_wallet_router

from wallet_helpers import build_user


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

    async def rollback(self):
        self._session.rollback()

    async def refresh(self, obj):
        self._session.refresh(obj)

    async def flush(self):
        self._session.flush()

    async def close(self):
        self._session.close()


@pytest.fixture
def api_client() -> Generator[Tuple[TestClient, object, sessionmaker], None, None]:
    app = FastAPI()
    add_exception_handler(app, new_exception_handler())
    app.include_router(referral_wallet_router, prefix="/private/v1")
    add_pagination(app)

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    Base.metadata.create_all(bind=engine)
    testing_session = sessionmaker(bind=engine, expire_on_commit=False, class_=Session)

    async def override_get_db() -> AsyncGenerator:
        sync_session = testing_session()
        fake_session = FakeAsyncSession(sync_session)
        try:
            yield fake_session
        finally:
            await fake_session.close()

    app.dependency_overrides[get_db] = override_get_db

    class UserContext:
        def __init__(self):
            self.user = build_user("default-user", [Permissions.REFERRAL_WALLET_OWN_READ.value])

    user_context = UserContext()
    app.dependency_overrides[auth_get_user] = lambda: user_context.user

    with TestClient(app) as client:
        yield client, user_context, testing_session

    Base.metadata.drop_all(bind=engine)
    engine.dispose()
