from fastapi import APIRouter

from router.v1.account_management import account_management_router, plan_management_router
from router.v1.account_management.plan_public import plan_public_router

public_router = APIRouter(prefix='/v1')

public_router.include_router(plan_public_router)