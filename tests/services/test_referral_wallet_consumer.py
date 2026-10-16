import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

from services.rabbit_service.referral_wallet_consumer import ReferralWalletConsumer
from services.rabbit_service.routing_keys import RoutingKeys


def _message(routing_key, payload):
    message = MagicMock()
    message.body = json.dumps({"payload": payload}).encode()
    message.routing_key = routing_key
    return message


def _consumer():
    factory = MagicMock()
    session = AsyncMock()
    factory.return_value.__aenter__ = AsyncMock(return_value=session)
    factory.return_value.__aexit__ = AsyncMock(return_value=False)
    return ReferralWalletConsumer(factory, MagicMock(), [member.value for member in RoutingKeys], prefetch_count=1)


def test_approved_event_credits_reward():
    async def body():
        consumer = _consumer()
        payload = {
            "referrer_uuid": "user-1",
            "reward_id": 4,
            "amount_cents": 1000,
            "external_purchase_id": "p-4",
            "admin_uuid": None,
            "note": None,
        }
        with patch("services.rabbit_service.referral_wallet_consumer.WalletService") as service_cls:
            service_cls.return_value.credit_reward = AsyncMock()
            await consumer.process_message(_message(RoutingKeys.REWARD_APPROVED, payload))
            service_cls.return_value.credit_reward.assert_awaited_once_with(
                referrer_uuid="user-1",
                reward_id=4,
                amount_cents=1000,
                external_purchase_id="p-4",
                admin_uuid=None,
                note=None,
            )

    asyncio.run(body())
