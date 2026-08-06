from unittest.mock import AsyncMock

import pytest
from test_wps_authentication import NOW, server_session

from tree_creative_api.infrastructure.auth_storage import (
    RedisLoginTransactionStore,
    RedisSessionStore,
)
from tree_creative_api.modules.auth.domain import LoginTransaction


@pytest.mark.asyncio
async def test_redis_login_state_uses_nx_and_atomic_getdel() -> None:
    redis = AsyncMock()
    store = RedisLoginTransactionStore(redis, "tree-creative:test:auth")
    transaction = LoginTransaction(
        redirect_uri="http://localhost:8000/api/oauth/callback",
        return_path="/organization",
        created_at=NOW,
    )

    await store.create("single-use-state", transaction, 600)
    stored_payload = redis.set.await_args.args[1]
    redis.getdel.return_value = stored_payload
    consumed = await store.consume("single-use-state")

    assert consumed == transaction
    redis.set.assert_awaited_once_with(
        "tree-creative:test:auth:login:single-use-state",
        stored_payload,
        ex=600,
        nx=True,
    )
    redis.getdel.assert_awaited_once_with("tree-creative:test:auth:login:single-use-state")


@pytest.mark.asyncio
async def test_redis_session_replacement_is_one_atomic_write() -> None:
    redis = AsyncMock()
    redis.set.return_value = True
    store = RedisSessionStore(redis, "tree-creative:test:auth")
    session = server_session()

    assert await store.replace(session)

    redis.set.assert_awaited_once_with(
        f"tree-creative:test:auth:session:{session.id}",
        session.model_dump_json(by_alias=True),
        xx=True,
        keepttl=True,
    )
