import aiohttp
import mock
import pytest
from discord import Client

from topgg import WebhookManager


auth = "youshallnotpass"


@pytest.fixture
def webhook_manager():
    return WebhookManager(Client()).dbl_webhook("/dbl", auth).dsl_webhook("/dsl", auth)


def test_WebhookManager_routes(webhook_manager):
    assert len(webhook_manager._webhooks) == 2


@pytest.mark.asyncio
async def test_WebhookManager_run_method(webhook_manager):
    task = webhook_manager.run(5000)

    try:
        if not task.done():
            assert await task is None

        assert hasattr(webhook_manager, "_webserver")
    finally:
        await webhook_manager.close()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "headers, result, state",
    [({"authorization": auth}, 200, True), ({}, 401, False)],
)
async def test_WebhookManager_validates_auth(webhook_manager, headers, result, state):
    await webhook_manager.run(5000)

    dbl_state = dsl_state = False

    @webhook_manager.bot.event
    async def on_dbl_vote(data):
        nonlocal dbl_state
        dbl_state = True

    @webhook_manager.bot.event
    async def on_dsl_vote(data):
        nonlocal dsl_state
        dsl_state = True

    try:
        for path in ("dbl", "dsl"):
            async with aiohttp.request(
                "POST", f"http://localhost:5000/{path}", headers=headers, json={}
            ) as r:
                assert r.status == result

            assert locals()[f"{path}_state"] is state
    finally:
        await webhook_manager.close()
