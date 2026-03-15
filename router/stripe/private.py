from AuthTools import HeaderUser
from AuthTools.Permissions.dependencies import require_permissions
from fastapi import APIRouter, Depends, status
from fastapi_problem import error as problem
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from config import Permissions
from database.crud.payment import PaymentService
from database.crud.plan import PlanService
from database.db.session import get_db
from database.schemas.payment import PaymentCreate, PaymentStatus, Purposes


stripe_private_router = APIRouter()


class StripeCreateCheckoutSessionPayload(BaseModel):
    plan_id: int
    success_url: str = "https://google.com"
    cancel_url: str = "https://google.com"


class StripeCheckoutSessionResponse(BaseModel):
    checkout_url: str
    session_id: str


@stripe_private_router.post(
    "/create-checkout-session",
    status_code=status.HTTP_201_CREATED,
    response_model=StripeCheckoutSessionResponse,
    description=f"Create Stripe checkout session for plan, required permissions: {Permissions.ACCOUNT_ALL_WRITE.value}",
)
async def stripe_create_checkout_session(
    payload: StripeCreateCheckoutSessionPayload,
    db: AsyncSession = Depends(get_db),
    user: HeaderUser = Depends(require_permissions(Permissions.ACCOUNT_ALL_WRITE))
):
    plan_service = PlanService(db)
    plan = await plan_service.get(payload.plan_id)
    if not plan:
        raise problem.NotFoundProblem(detail="Plan not found")

    from services.stripe_service.service import StripeService
    from services.stripe_service.types import Product, Price, ProductData

    stripe_service = StripeService(
        success_url=payload.success_url,
        cancel_url=payload.cancel_url
    )

    product = Product(
        price_data=Price(
            product_data=ProductData(
                name=plan.name,
                description=plan.description or f"Purchase plan {plan.name}"
            ),
            unit_amount=int(plan.price * 100)  # Stripe expects amount in cents
        ),
        quantity=1
    )

    try:
        session = stripe_service.create_checkout_session(
            product=product,
            metadata={
                "plan_id": str(plan.id),
                "user_uuid": user.uuid,
                "purpose": Purposes.PLAN_PURCHASE.value
            }
        )
    except Exception as e:
        raise problem.ServerProblem(detail=f"Unable to create Stripe checkout session: {str(e)}")

    payment_service = PaymentService(db)
    await payment_service.create(
        PaymentCreate(
            user_external_id=user.uuid,
            source="web",
            provider="STRIPE",
            amount=plan.price,
            purpose=Purposes.PLAN_PURCHASE,
            purpose_external_id=str(plan.id),
            provider_payment_id=session.id,
            status=PaymentStatus.PENDING,
        )
    )

    return StripeCheckoutSessionResponse(
        checkout_url=session.url,
        session_id=session.id
    )




