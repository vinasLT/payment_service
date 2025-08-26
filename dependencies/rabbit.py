from typing import AsyncGenerator

from services.rabbit_service import RabbitMQPublisher


async def get_rabbit_mq_service() -> AsyncGenerator[RabbitMQPublisher, None]:
    service = RabbitMQPublisher()
    await service.connect()
    try:
        yield service
    finally:
        await service.close()