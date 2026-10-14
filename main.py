import asyncio
from contextlib import asynccontextmanager

import uvicorn
from aio_pika import connect_robust
from fastapi import FastAPI, APIRouter
from fastapi_pagination import add_pagination
from fastapi_problem.handler import new_exception_handler, add_exception_handler

from config import settings
from core.logger import logger
from database.db.session import AsyncSessionLocal
from router.health import health_router
from services.rabbit_service.referral_wallet_consumer import ReferralWalletConsumer
from services.rabbit_service.routing_keys import RoutingKeys
from router.paypal.private import paypal_private_router
from router.stripe.private import stripe_private_router
from router.stripe.public import stripe_public_router
from router.v1.private import private_router
from router.v1.public import public_router

docs_url = "/docs" if settings.enable_docs else None
redoc_url = "/redoc"  if settings.enable_docs else None
openapi_url = "/openapi.json" if settings.enable_docs else None


@asynccontextmanager
async def lifespan(_: FastAPI):
    max_attempts = 5
    base_delay_s = 2
    connection = None
    for attempt in range(1, max_attempts + 1):
        try:
            connection = await connect_robust(settings.RABBITMQ_URL)
            break
        except Exception:
            if attempt >= max_attempts:
                raise
            delay = base_delay_s * attempt
            logger.warning(
                "RabbitMQ connection failed, retrying",
                extra={"attempt": attempt, "delay_s": delay},
            )
            await asyncio.sleep(delay)

    if connection is None:
        raise RuntimeError("RabbitMQ connection not established after retries")
    consumer = ReferralWalletConsumer(
        AsyncSessionLocal,
        connection,
        [member.value for member in RoutingKeys],
        prefetch_count=1,
    )
    await consumer.set_up()
    await consumer.start_consuming()

    logger.info(f"{settings.APP_NAME} started!")
    yield
    await consumer.stop_consuming()


app = FastAPI(title='Payment Service',
              description='Process payments via Stripe, Paypal',
              version='0.0.1',
              root_path=settings.ROOT_PATH,
              docs_url=docs_url,
              redoc_url=redoc_url,
              openapi_url=openapi_url,
              lifespan=lifespan)

eh = new_exception_handler()
add_exception_handler(app, eh)


public_endpoints = APIRouter(prefix="/public", tags=["Public"])
private_endpoints = APIRouter(prefix="/private")

# stripe
public_endpoints.include_router(stripe_public_router, prefix="/stripe", tags=["Stripe"])
private_endpoints.include_router(stripe_private_router, prefix="/stripe", tags=["Stripe"])

# paypal
private_endpoints.include_router(paypal_private_router, prefix="/paypal", tags=["Paypal"])

private_endpoints.include_router(private_router)
public_endpoints.include_router(public_router)

app.include_router(public_endpoints)
app.include_router(private_endpoints)

app.include_router(health_router)
add_pagination(app)


if __name__ == '__main__':
    uvicorn.run(app, host="localhost", port=8002)
