# -*- coding: utf-8 -*-

# The MIT License (MIT)

# Copyright (c) 2021 Assanali Mukhanov
# Copyright (c) 2024 null8626

# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.

__all__ = ["HTTPClient"]

import asyncio
import json
import logging
import sys
import warnings
from datetime import datetime
from typing import Any, Coroutine, Dict, Iterable, List, Optional, Sequence, Union, cast

import aiohttp
from aiohttp import ClientResponse

from . import __version__, errors
from .ratelimiter import AsyncRateLimiter, AsyncRateLimiterManager

_LOGGER = logging.getLogger("topgg.http")


async def _json_or_text(
    response: ClientResponse,
) -> Union[dict, str]:
    text = await response.text()
    if response.headers["Content-Type"] == "application/json; charset=utf-8":
        return json.loads(text)
    return text


class HTTPClient:
    """Represents an HTTP client sending HTTP requests to the Top.gg API.

    .. _aiohttp session: https://aiohttp.readthedocs.io/en/stable/client_reference.html#client-session

    Args:
        token (str)
            A Top.gg API Token.

    Keyword Arguments:
        session: `aiohttp session`_
            The `aiohttp session`_ used for requests to the API.
        **kwargs:
            Arbitrary kwargs to be passed to :class:`aiohttp.ClientSession`.
    """

    def __init__(
        self,
        token: str,
        *,
        session: Optional[aiohttp.ClientSession] = None,
        **kwargs: Any,
    ) -> None:
        self.BASE = "https://top.gg/api"
        self.token = token
        self._own_session = session is None
        self.session: aiohttp.ClientSession = session or aiohttp.ClientSession(**kwargs)
        self.global_rate_limiter = AsyncRateLimiter(max_calls=99, period=1, callback=_rate_limit_handler)
        self.bot_rate_limiter = AsyncRateLimiter(max_calls=59, period=60, callback=_rate_limit_handler)
        self.rate_limiters = AsyncRateLimiterManager([self.global_rate_limiter, self.bot_rate_limiter])
        self.user_agent = (
            f"topggpy (https://github.com/top-gg-community/python-sdk {__version__}) Python/"
            f"{sys.version_info[0]}.{sys.version_info[1]} aiohttp/{aiohttp.__version__}"
        )

    async def request(self, method: str, endpoint: str, **kwargs: Any) -> dict:
        """Handles requests to the API."""
        rate_limiters = self.rate_limiters if endpoint.startswith("/bots") else self.global_rate_limiter
        url = f"{self.BASE}{endpoint}"

        if not self.token:
            raise errors.UnauthorizedDetected("Top.gg API token not provided")

        headers = {
            "User-Agent": self.user_agent,
            "Content-Type": "application/json",
            "Authorization": self.token,
        }

        if "json" in kwargs:
            kwargs["data"] = to_json(kwargs.pop("json"))

        kwargs["headers"] = headers

        for _ in range(2):
            async with rate_limiters:  # type: ignore
                async with self.session.request(method, url, **kwargs) as resp:
                    _LOGGER.debug(
                        "%s %s with %s has returned %s",
                        method,
                        url,
                        kwargs.get("data"),
                        resp.status,
                    )

                    data = await _json_or_text(resp)

                    if 300 > resp.status >= 200:
                        return cast(dict, data)

                    elif resp.status == 429:  # we are being ratelimited
                        fmt = "We are being ratelimited. Retrying in %.2f seconds (%.3f minutes)."

                        # sleep a bit
                        retry_after = float(resp.headers["Retry-After"])
                        mins = retry_after / 60
                        _LOGGER.warning(fmt, retry_after, mins)

                        # check if it's a global ratelimit (True as only 1 ratelimit atm - /api/bots)
                        # is_global = True
                        # is_global = data.get('global', False)
                        # if is_global:
                        #     self._global_over.clear()

                        await asyncio.sleep(retry_after)
                        _LOGGER.debug("Done sleeping for the ratelimit. Retrying...")

                        # release the global lock now that the
                        # global ratelimit has passed
                        # if is_global:
                        #     self._global_over.set()
                        _LOGGER.debug("Global ratelimit is now over.")
                        continue

                    elif resp.status == 400:
                        raise errors.HTTPException(resp, data)
                    elif resp.status == 401:
                        raise errors.Unauthorized(resp, data)
                    elif resp.status == 403:
                        raise errors.Forbidden(resp, data)
                    elif resp.status == 404:
                        raise errors.NotFound(resp, data)
                    elif resp.status >= 500:
                        raise errors.ServerError(resp, data)

        # We've run out of retries, raise.
        raise errors.HTTPException(resp, data)

    async def close(self) -> None:
        if self._own_session:
            await self.session.close()

    async def post_guild_count(
        self,
        guild_count: Optional[Union[int, List[int]]],
        shard_count: Optional[int],
        shard_id: Optional[int],
    ) -> None:
        """Posts bot's guild count and shards info on Top.gg."""
        payload = {"server_count": guild_count}
        if shard_count:
            payload["shard_count"] = shard_count
        if shard_id:
            payload["shard_id"] = shard_id

        await self.request("POST", "/bots/stats", json=payload)

    def get_weekend_status(self) -> Coroutine[Any, Any, dict]:
        """Gets the weekend status from Top.gg."""
        return self.request("GET", "/weekend")

    def get_guild_count(self, bot_id: int) -> Coroutine[Any, Any, dict]:
        """Gets the guild count of the given Bot ID."""
        return self.request("GET", f"/bots/{bot_id}/stats")

    def get_bot_info(self, bot_id: int) -> Coroutine[Any, Any, dict]:
        """Gets the information of a bot under given bot ID on Top.gg."""
        return self.request("GET", f"/bots/{bot_id}")

    def get_bot_votes(self, bot_id: int) -> Coroutine[Any, Any, Iterable[dict]]:
        """Gets your bot's last 1000 votes on Top.gg."""
        return self.request("GET", f"/bots/{bot_id}/votes")

    def get_bots(
        self,
        limit: int,
        offset: int,
        sort: str,
        search: Dict[str, str],
        fields: Sequence[str],
    ) -> Coroutine[Any, Any, dict]:
        """
        Warning:
            This function is deprecated.
        """

        warnings.warn("get_bots is now deprecated.", DeprecationWarning)

        limit = min(limit, 500)
        fields = ", ".join(fields)
        search = " ".join([f"{field}: {value}" for field, value in search.items()])

        return self.request(
            "GET",
            "/bots",
            params={
                "limit": limit,
                "offset": offset,
                "sort": sort,
                "search": search,
                "fields": fields,
            },
        )

    def get_user_info(self, user_id: int) -> Coroutine[Any, Any, dict]:
        """Gets an object of the user on Top.gg."""
        return self.request("GET", f"/users/{user_id}")

    def get_user_vote(self, bot_id: int, user_id: int) -> Coroutine[Any, Any, dict]:
        """Gets info whether the user has voted for your bot."""
        return self.request("GET", f"/bots/{bot_id}/check", params={"userId": user_id})


async def _rate_limit_handler(until: float) -> None:
    """Handles the displayed message when we are ratelimited."""
    duration = round(until - datetime.utcnow().timestamp())
    mins = duration / 60
    fmt = "We have exhausted a ratelimit quota. Retrying in %.2f seconds (%.3f minutes)."
    _LOGGER.warning(fmt, duration, mins)


def to_json(obj: Any) -> str:
    if json.__name__ == "ujson":
        return json.dumps(obj, ensure_ascii=True)
    return json.dumps(obj, separators=(",", ":"), ensure_ascii=True)
