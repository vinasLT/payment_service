from AuthTools.Permissions.dependencies import require_permissions
from fastapi import APIRouter, Response, status
from fastapi.params import Depends
from fastapi_pagination import Params
from fastapi_pagination.ext.sqlalchemy import apaginate
from fastapi_problem import error as problem
from sqlalchemy.ext.asyncio import AsyncSession

from config import Permissions
from database.crud import PlanService, TransactionService, UserAccountService
from database.db.session import get_db
from database.schemas.plan import PlanCreate, PlanRead, PlanUpdate
from database.schemas.transaction import TransactionCreate
from database.schemas.user_account import UserAccountUpdate
from database.models.transaction import TransactionType
from schemas.account import UserAccountDetailed
from schemas.plan import PlanAssignPayload, PlansPage


plan_management_router = APIRouter(prefix='/plan', tags=['Plan Management'])

class PlanParams(Params):
    size: int = 10

@plan_management_router.get(
    "",
    response_model=PlansPage,
    description=f"List plans, required permissions: {Permissions.PLAN_ALL_READ.value}",
    dependencies=[Depends(require_permissions(Permissions.PLAN_ALL_READ))],
)
async def list_plans(
    params: PlanParams = Depends(),
    db: AsyncSession = Depends(get_db),
):
    service = PlanService(db)
    plans_query = await service.get_all(get_stmt=True)
    return await apaginate(db, plans_query, params)


@plan_management_router.post(
    "",
    response_model=PlanRead,
    status_code=status.HTTP_201_CREATED,
    description=f"Create plan, required permissions: {Permissions.PLAN_ALL_WRITE.value}",
    dependencies=[Depends(require_permissions(Permissions.PLAN_ALL_WRITE))],
)
async def create_plan(plan_in: PlanCreate, db: AsyncSession = Depends(get_db)):
    service = PlanService(db)
    return await service.create(plan_in)


@plan_management_router.get(
    "/{plan_id}",
    response_model=PlanRead,
    description=f"Get plan, required permissions: {Permissions.PLAN_ALL_READ.value}",
    dependencies=[Depends(require_permissions(Permissions.PLAN_ALL_READ))],
)
async def get_plan(plan_id: int, db: AsyncSession = Depends(get_db)):
    service = PlanService(db)
    plan = await service.get(plan_id)
    if not plan:
        raise problem.NotFoundProblem(detail="Plan not found")
    return plan


@plan_management_router.put(
    "/{plan_id}",
    response_model=PlanRead,
    description=f"Update plan, required permissions: {Permissions.PLAN_ALL_WRITE.value}",
    dependencies=[Depends(require_permissions(Permissions.PLAN_ALL_WRITE))],
)
async def update_plan(plan_id: int, plan_in: PlanUpdate, db: AsyncSession = Depends(get_db)):
    service = PlanService(db)
    update_payload = plan_in.model_dump(exclude_unset=True)
    if not update_payload:
        raise problem.BadRequestProblem(detail="No fields provided for update")
    plan = await service.update(plan_id, plan_in)
    if not plan:
        raise problem.NotFoundProblem(detail="Plan not found")
    return plan


@plan_management_router.delete(
    "/{plan_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    description=f"Delete plan, required permissions: {Permissions.PLAN_ALL_DELETE.value}",
    dependencies=[Depends(require_permissions(Permissions.PLAN_ALL_DELETE))],
)
async def delete_plan(plan_id: int, db: AsyncSession = Depends(get_db)):
    service = PlanService(db)
    deleted = await service.delete(plan_id)
    if not deleted:
        raise problem.NotFoundProblem(detail="Plan not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@plan_management_router.post(
    "/assign",
    response_model=UserAccountDetailed,
    description=f"Assign plan to user account,"
                f" required permissions: {Permissions.PLAN_ALL_WRITE.value, Permissions.ACCOUNT_ALL_WRITE.value}",
    dependencies=[Depends(require_permissions(Permissions.PLAN_ALL_WRITE, Permissions.ACCOUNT_ALL_WRITE))],
)
async def assign_plan_to_account(
    payload: PlanAssignPayload, db: AsyncSession = Depends(get_db)
):
    plan_service = PlanService(db)
    plan = await plan_service.get(payload.plan_id)
    if not plan:
        raise problem.NotFoundProblem(detail="Plan not found")

    account_service = UserAccountService(db)
    transaction_service = TransactionService(db)
    account = await account_service.get_by_user_uuid(payload.user_uuid)

    account = await account_service.update(
        account.id, UserAccountUpdate(plan_id=plan.id)
    )

    await transaction_service.create(
        TransactionCreate(
            user_account_id=account.id,
            plan_id=plan.id,
            transaction_type=TransactionType.PLAN_PURCHASE,
            amount=plan.bid_power,
        )
    )

    account = await account_service.update(
        account.id,
        UserAccountUpdate(balance=account.balance + plan.bid_power),
    )

    return account
