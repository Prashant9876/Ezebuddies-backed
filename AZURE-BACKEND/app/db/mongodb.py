from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional

from app.core.config import settings


client: Optional[AsyncIOMotorClient] = None


async def connect_to_mongo() -> None:
    global client
    settings.validate()

    client = AsyncIOMotorClient(
        settings.mongo_uri,
        serverSelectionTimeoutMS=settings.mongo_server_selection_timeout_ms,
        connectTimeoutMS=settings.mongo_connect_timeout_ms,
        socketTimeoutMS=settings.mongo_socket_timeout_ms,
        retryWrites=True,
    )
    await client.admin.command("ping")
    await _ensure_indexes()


async def _ensure_indexes() -> None:
    mongo_client = get_client()
    reset_collection = mongo_client[settings.login_db_name][
        settings.reset_password_collection
    ]

    # TTL index: document will be auto-deleted when expires_at time is reached.
    await reset_collection.create_index("expires_at", expireAfterSeconds=0)
    await reset_collection.create_index("user_id")
    await reset_collection.create_index("token_hash", unique=True)


async def close_mongo_connection() -> None:
    global client
    if client is not None:
        client.close()
    client = None


def get_client() -> AsyncIOMotorClient:
    if client is None:
        raise RuntimeError("MongoDB connection is not initialized")
    return client
