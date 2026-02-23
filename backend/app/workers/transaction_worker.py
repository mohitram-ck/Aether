import asyncio
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update
from app.core.database import AsyncSessionLocal
from app.core.redis_client import get_redis
from app.models.transaction import Transaction
import uuid

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

STREAM_NAME = "transactions_stream"
CONSUMER_GROUP = "transaction_workers"
CONSUMER_NAME = "worker-1"
BATCH_SIZE = 50
POLL_INTERVAL = 0.5


async def create_consumer_group(redis):
    try:
        await redis.xgroup_create(STREAM_NAME, CONSUMER_GROUP, id="0", mkstream=True)
        logger.info(f"Consumer group '{CONSUMER_GROUP}' created")
    except Exception as e:
        if "BUSYGROUP" in str(e):
            logger.info(f"Consumer group '{CONSUMER_GROUP}' already exists")
        else:
            raise e


async def process_batch(messages: list, db: AsyncSession):
    transaction_ids = []
    try:
        for message_id, fields in messages:
            txn_id = fields.get("transaction_id")
            if txn_id:
                await db.execute(
                    update(Transaction)
                    .where(Transaction.id == uuid.UUID(txn_id))
                    .values(status="processed")
                )
                transaction_ids.append((message_id, txn_id))

        await db.commit()
        logger.info(f"Batch committed: {len(transaction_ids)} transactions processed")
        return transaction_ids

    except Exception as e:
        await db.rollback()
        logger.error(f"Batch failed, rolling back: {e}")
        return []


async def acknowledge_messages(redis, message_ids: list):
    for msg_id, txn_id in message_ids:
        await redis.xack(STREAM_NAME, CONSUMER_GROUP, msg_id)
        logger.info(f"Acknowledged message {msg_id} for transaction {txn_id}")


async def run_worker():
    logger.info("Transaction worker starting...")
    redis = await get_redis()
    await create_consumer_group(redis)

    logger.info("Worker listening on Redis Stream...")

    while True:
        try:
            messages = await redis.xreadgroup(
                groupname=CONSUMER_GROUP,
                consumername=CONSUMER_NAME,
                streams={STREAM_NAME: ">"},
                count=BATCH_SIZE,
                block=500
            )

            if not messages:
                await asyncio.sleep(POLL_INTERVAL)
                continue

            stream_messages = messages[0][1]

            if not stream_messages:
                await asyncio.sleep(POLL_INTERVAL)
                continue

            logger.info(f"Pulled {len(stream_messages)} messages from stream")

            async with AsyncSessionLocal() as db:
                processed = await process_batch(stream_messages, db)
                if processed:
                    await acknowledge_messages(redis, processed)

        except Exception as e:
            logger.error(f"Worker error: {e}")
            await asyncio.sleep(1)


if __name__ == "__main__":
    asyncio.run(run_worker())