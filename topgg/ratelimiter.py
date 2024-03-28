# -*- coding: utf-8 -*-

# The MIT License (MIT)

# Copyright (c) 2021 Assanali Mukhanov

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

import asyncio
import collections
from datetime import datetime
from types import TracebackType
from typing import Any, Awaitable, Callable, List, Optional, Type


class AsyncRateLimiter:
    """
    Provides rate limiting for an operation with a configurable number of requests for a time period.
    """

    __lock: asyncio.Lock
    callback: Optional[Callable[[float], Awaitable[Any]]]
    max_calls: int
    period: float
    calls: collections.deque

    def __init__(
        self,
        max_calls: int,
        period: float = 1.0,
        callback: Optional[Callable[[float], Awaitable[Any]]] = None,
    ):
        if period <= 0:
            raise ValueError("Rate limiting period should be > 0")
        if max_calls <= 0:
            raise ValueError("Rate limiting number of calls should be > 0")
        self.calls = collections.deque()

        self.period = period
        self.max_calls = max_calls
        self.callback = callback
        self.__lock = asyncio.Lock()

    async def __aenter__(self) -> "AsyncRateLimiter":
        async with self.__lock:
            if len(self.calls) >= self.max_calls:
                until = datetime.utcnow().timestamp() + self.period - self._timespan
                if self.callback:
                    asyncio.ensure_future(self.callback(until))
                sleep_time = until - datetime.utcnow().timestamp()
                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)
            return self

    async def __aexit__(
        self,
        exc_type: Type[BaseException],
        exc_val: BaseException,
        exc_tb: TracebackType,
    ) -> None:
        async with self.__lock:
            # Store the last operation timestamp.
            self.calls.append(datetime.utcnow().timestamp())

            while self._timespan >= self.period:
                self.calls.popleft()

    @property
    def _timespan(self) -> float:
        return self.calls[-1] - self.calls[0]


class AsyncRateLimiterManager:
    rate_limiters: List[AsyncRateLimiter]

    def __init__(self, rate_limiters: List[AsyncRateLimiter]):
        self.rate_limiters = rate_limiters

    async def __aenter__(self) -> "AsyncRateLimiterManager":
        [await manager.__aenter__() for manager in self.rate_limiters]
        return self

    async def __aexit__(
        self,
        exc_type: Type[BaseException],
        exc_val: BaseException,
        exc_tb: TracebackType,
    ) -> None:
        await asyncio.gather(*[manager.__aexit__(exc_type, exc_val, exc_tb) for manager in self.rate_limiters])
