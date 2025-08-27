from fastapi import APIRouter, Depends
import json
import stripe
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from fastapi import Request, Header
from fastapi.responses import JSONResponse

from core.logger import logger
from database.crud.payment import PaymentService
from database.db.session import get_db
from database.models.payment import Payment
from database.schemas.payment import Purposes, PaymentUpdate, PaymentStatus
from services.rabbit_service import RabbitMQPublisher
from services.stripe_service.service import StripeService


stripe_public_router = APIRouter()

@stripe_public_router.post("/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(alias="Stripe-Signature"),
    db: AsyncSession = Depends(get_db)
):
    payload = await request.body()
    try:
        event = json.loads(payload)
    except json.JSONDecodeError:
        return JSONResponse({"success": False})

    if settings.STRIPE_WEBHOOK_SECRET:
        try:
            event = stripe.Webhook.construct_event(
                payload=payload,
                sig_header=stripe_signature,
                secret=settings.STRIPE_WEBHOOK_SECRET,
            )
        except stripe.error.SignatureVerificationError:
            return JSONResponse({"success": False})

    event_type = event["type"]

    payment_service = PaymentService(db)

    data = StripeService.decode_webhook(event)
    session: Payment = await payment_service.get_by_provider_payment_id(data.checkout_id)
    if event_type == "checkout.session.completed":
        logger.info(f"Checkout session completed event received")
        if session.status != PaymentStatus.COMPLETED:
            await payment_service.update(
                session.id, PaymentUpdate(status=PaymentStatus.COMPLETED)
            )
            rabbit_service = RabbitMQPublisher()
            routing_key = f'payment.success.{session.purpose}'.lower()
            logger.info(f"Routing key: {routing_key}")

            if session.purpose == Purposes.CARFAX:
                payload = {
                    "session_id": session.id,
                    "user_uuid": session.user_external_id,
                    "amount": session.amount,
                    "purpose": session.purpose,
                    "purpose_external_id": session.purpose_external_id,
                }
                logger.info(f"Payload: {payload}")
                await rabbit_service.publish(routing_key=routing_key, payload=payload)


    elif event_type == "checkout.session.expired":
        await payment_service.update(session.id, PaymentUpdate(status=PaymentStatus.FAILED))
    return JSONResponse({"success": True})