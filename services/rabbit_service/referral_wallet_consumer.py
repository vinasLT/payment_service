import json

from aio_pika.abc import AbstractIncomingMessage
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from core.logger import logger
from services.rabbit_service.base import RabbitBaseService
from services.rabbit_service.routing_keys import RoutingKeys
from services.referral_wallet.wallet_service import WalletService


class ReferralWalletConsumer(RabbitBaseService):
    def __init__(self, db_session_factory: async_sessionmaker[AsyncSession], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.db_session_factory = db_session_factory

    async def process_message(self, message: AbstractIncomingMessage):
        payload = json.loads(message.body.decode("utf-8")).get("payload")
        routing_key = message.routing_key
        logger.info("Received new message", extra={"routing_key": routing_key, "payload": payload})
        if not isinstance(payload, dict):
            raise ValueError("Message payload must be a JSON object")

        async with self.db_session_factory() as session:
            wallet_service = WalletService(session)
            if routing_key == RoutingKeys.REWARD_APPROVED:
                await wallet_service.credit_reward(
                    referrer_uuid=payload["referrer_uuid"],
                    reward_id=payload["reward_id"],
                    amount_cents=payload["amount_cents"],
                    external_purchase_id=payload.get("external_purchase_id"),
                    admin_uuid=payload.get("admin_uuid"),
                    note=payload.get("note"),
                )
            else:
                logger.warning("No handler for routing key", extra={"routing_key": routing_key})
