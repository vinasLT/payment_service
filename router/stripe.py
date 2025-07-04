from fastapi import APIRouter, Body
import json
import stripe
from pydantic import HttpUrl

from config import STRIPE_WEBHOOK_SECRET, CARFAX_SERVICE_URL
from fastapi import Request, Header, HTTPException
from fastapi.responses import JSONResponse

from database.crud.payment import PaymentService
from database.schemas.payment import Purposes, PaymentCreate, PaymentUpdate, PaymentStatus
from schemas import StripeCheckOutIn, StripeCheckOutOut
from services.request_webhook import send_request_to_webhook
from stripe_service.service import StripeService

stripe_router = APIRouter()


@stripe_router.post("/get-checkout", response_model=StripeCheckOutOut)
async def get_checkout(data: StripeCheckOutIn = Body(...)):
    if data.purpose == Purposes.CARFAX:
        product = StripeService.CARFAX
    else:
        raise HTTPException(400, 'Wrong Purpose')

    stripe_service = StripeService(success_url=str(data.success_link), cancel_url=str(data.cancel_link))
    session = stripe_service.create_checkout_session(product)
    async with PaymentService() as payment:
        await payment.create(PaymentCreate(user_external_id=data.external_user_id, source=data.source,
                                           provider='STRIPE', amount=product.price_data.unit_amount,
                                           purpose=product.price_data.product_data.name,
                                           provider_payment_id=session.id, purpose_external_id=data.purpose_external_id,))

    return StripeCheckOutOut(link=HttpUrl(session.url))

@stripe_router.post("/webhook")
async def stripe_webhook(request: Request, stripe_signature: str = Header(None)):
    payload = await request.body()

    try:
        event = json.loads(payload)
    except json.JSONDecodeError:
        return JSONResponse(content={"success": False})

    if STRIPE_WEBHOOK_SECRET:
        if not stripe_signature:
            raise HTTPException(status_code=400, detail="Missing stripe-signature header")
        try:
            event = stripe.Webhook.construct_event(
                payload=payload,
                sig_header=stripe_signature,
                secret=STRIPE_WEBHOOK_SECRET
            )
        except stripe.error.SignatureVerificationError:
            return JSONResponse(content={"success": False})

    event_type = event['type']
    data = StripeService.decode_webhook(event)
    async with PaymentService() as payment:
        session = await payment.get_by_provider_payment_id(data.checkout_id)
        if event_type == 'checkout.session.completed':
            await payment.update(session.id, PaymentUpdate(status=PaymentStatus.COMPLETED))
            if session.purpose == Purposes.CARFAX:
                await send_request_to_webhook(f'{CARFAX_SERVICE_URL}internal/carfax/webhook/{session.purpose_external_id}/paid')
        elif event_type == 'checkout.session.expired':
            await payment.update(session.id, PaymentUpdate(status=PaymentStatus.FAILED))

    return JSONResponse(content={"success": True})