import datetime

import mock
import pytest
from aiohttp import ClientSession
from pytest_mock import MockerFixture

from topgg import DBLClient
from topgg.autopost import AutoPoster
from topgg.errors import ServerError, TopGGException, Unauthorized


MOCK_TOKEN = "amogus.eyJpZCI6IjEwMjY1MjU1NjgzNDQyNjQ3MjQiLCJib3QiOnRydWUsImlhdCI6MTY5OTk4NDYyM30.amogus"


@pytest.fixture
def session() -> ClientSession:
    return mock.Mock(ClientSession)


@pytest.fixture
def autopost(session: ClientSession) -> AutoPoster:
    return AutoPoster(DBLClient(MOCK_TOKEN, session=session))


@pytest.mark.asyncio
async def test_AutoPoster_breaks_autopost_loop_on_401(mocker: MockerFixture, session: ClientSession) -> None:
    response = mock.Mock("reason, status")
    response.reason = "Unauthorized"
    response.status = 401

    mocker.patch("topgg.DBLClient.post_guild_count", side_effect=Unauthorized(response, {}))

    callback = mock.Mock()
    autopost = DBLClient(MOCK_TOKEN, session=session).autopost().stats(callback)
    assert isinstance(autopost, AutoPoster)
    assert not isinstance(autopost.stats()(callback), AutoPoster)

    with pytest.raises(Unauthorized):
        await autopost.start()

    callback.assert_called_once()
    assert not autopost.is_running


@pytest.mark.asyncio
async def test_AutoPoster_raises_missing_stats(autopost: AutoPoster) -> None:
    with pytest.raises(TopGGException, match="you must provide a callback that returns the stats."):
        await autopost.start()


@pytest.mark.asyncio
async def test_AutoPoster_raises_already_running(autopost: AutoPoster) -> None:
    autopost.stats(mock.Mock()).start()
    with pytest.raises(TopGGException, match="the autopost is already running."):
        await autopost.start()


@pytest.mark.asyncio
async def test_AutoPoster_interval_too_short(autopost: AutoPoster) -> None:
    with pytest.raises(ValueError, match="interval must be greated than 900 seconds."):
        autopost.set_interval(50)


@pytest.mark.asyncio
async def test_AutoPoster_error_callback(mocker: MockerFixture, autopost: AutoPoster) -> None:
    error_callback = mock.Mock()
    response = mock.Mock("reason, status")
    response.reason = "Internal Server Error"
    response.status = 500
    side_effect = ServerError(response, {})

    mocker.patch("topgg.DBLClient.post_guild_count", side_effect=side_effect)
    task = autopost.on_error(error_callback).stats(mock.Mock()).start()
    autopost.stop()
    await task
    error_callback.assert_called_once_with(side_effect)


def test_AutoPoster_interval(autopost: AutoPoster):
    assert autopost.interval == 900
    autopost.set_interval(datetime.timedelta(hours=1))
    assert autopost.interval == 3600
    autopost.interval = datetime.timedelta(hours=2)
    assert autopost.interval == 7200
    autopost.interval = 3600
    assert autopost.interval == 3600
