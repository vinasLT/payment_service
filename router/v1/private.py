from fastapi import APIRouter

from router.v1.account_management import account_management_router, plan_management_router

private_router = APIRouter(prefix='/v1')

private_router.include_router(account_management_router)
private_router.include_router(plan_management_router)