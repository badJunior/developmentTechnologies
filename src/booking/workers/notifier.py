import asyncio
import json
import aio_pika
from booking.config import get_settings
from booking.adapters.rabbitmq_publisher import EXCHANGE

async def main():
    settings = get_settings()
    connection = await aio_pika.connect_robust(str(settings.broker_url))
    channel = await connection.channel()
    await channel.set_qos(prefetch_count=10)

    queue = await channel.declare_queue("booking.notifications", durable=True)
    exchange = await channel.declare_exchange(EXCHANGE, aio_pika.ExchangeType.TOPIC, durable=True)
    await queue.bind(exchange, routing_key="booking.*")

    print("Worker started, waiting for messages...")

    async def process(message):
        body = json.loads(message.body)
        print(f"Received: {message.routing_key} -> {body.get('booking_id')}")
        await message.ack()

    await queue.consume(process)
    await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
