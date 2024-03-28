import mock
import pytest
from aiohttp import ClientSession

import topgg
from topgg import errors


MOCK_TOKEN = "amogus.eyJpZCI6IjEwMjY1MjU1NjgzNDQyNjQ3MjQiLCJib3QiOnRydWUsImlhdCI6MTY5OTk4NDYyM30.amogus"


@pytest.fixture
def session() -> ClientSession:
    return mock.Mock(ClientSession)


@pytest.fixture
def client() -> topgg.DBLClient:
    client = topgg.DBLClient(token=MOCK_TOKEN)
    client.http = mock.Mock(topgg.http.HTTPClient)
    return client


@pytest.mark.asyncio
async def test_HTTPClient_with_external_session(session: ClientSession):
    http = topgg.http.HTTPClient(MOCK_TOKEN, session=session)
    assert not http._own_session
    await http.close()
    session.close.assert_not_called()


@pytest.mark.asyncio
async def test_HTTPClient_with_no_external_session(session: ClientSession):
    http = topgg.http.HTTPClient(MOCK_TOKEN)
    http.session = session
    assert http._own_session
    await http.close()
    session.close.assert_called_once()


@pytest.mark.asyncio
async def test_DBLClient_post_guild_count_with_no_args():
    client = topgg.DBLClient(MOCK_TOKEN)
    with pytest.raises(TypeError, match="stats or guild_count must be provided."):
        await client.post_guild_count()


@pytest.mark.asyncio
async def test_closed_DBLClient_raises_exception():
    client = topgg.DBLClient(MOCK_TOKEN)
    assert not client.is_closed
    await client.close()
    assert client.is_closed
    with pytest.raises(errors.ClientException, match="client has been closed."):
        await client.get_weekend_status()


@pytest.mark.asyncio
async def test_DBLClient_bot_id():
    client = topgg.DBLClient(MOCK_TOKEN)
    assert not client.is_closed
    assert client.bot_id == 1026525568344264724
    await client.close()
    assert client.is_closed


@pytest.mark.asyncio
async def test_DBLClient_get_weekend_status(client: topgg.DBLClient):
    client.http.get_weekend_status = mock.AsyncMock()
    await client.get_weekend_status()
    client.http.get_weekend_status.assert_called_once()


@pytest.mark.asyncio
async def test_DBLClient_post_guild_count(client: topgg.DBLClient):
    client.http.post_guild_count = mock.AsyncMock()
    await client.post_guild_count(guild_count=123)
    client.http.post_guild_count.assert_called_once()


@pytest.mark.asyncio
async def test_DBLClient_get_guild_count(client: topgg.DBLClient):
    client.http.get_guild_count = mock.AsyncMock(return_value={})
    await client.get_guild_count()
    client.http.get_guild_count.assert_called_once()


@pytest.mark.asyncio
async def test_DBLClient_get_bot_votes(client: topgg.DBLClient):
    client.http.get_bot_votes = mock.AsyncMock(return_value=[])
    await client.get_bot_votes()
    client.http.get_bot_votes.assert_called_once()


@pytest.mark.asyncio
async def test_DBLClient_get_user_info(client: topgg.DBLClient):
    client.http.get_user_info = mock.AsyncMock(return_value={})
    await client.get_user_info(1234)
    client.http.get_user_info.assert_called_once()


@pytest.mark.asyncio
async def test_DBLClient_get_user_vote(client: topgg.DBLClient):
    client.http.get_user_vote = mock.AsyncMock(return_value={"voted": 1})
    await client.get_user_vote(1234)
    client.http.get_user_vote.assert_called_once()
