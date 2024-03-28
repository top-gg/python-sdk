# The MIT License (MIT)

# Copyright (c) 2021 Norizon

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

__all__ = ["AutoPoster"]

import asyncio
import datetime
import sys
import traceback
import typing as t

from topgg import errors

from .types import StatsWrapper

if t.TYPE_CHECKING:
    import asyncio

    from .client import DBLClient

CallbackT = t.Callable[..., t.Any]
StatsCallbackT = t.Callable[[], StatsWrapper]


class AutoPoster:
    """
    A helper class for autoposting. Takes in a :obj:`~.client.DBLClient` to instantiate.

    Note:
        You should not instantiate this unless you know what you're doing.
        Generally, you'd better use the :meth:`~.client.DBLClient.autopost` method.

    Args:
        client (:obj:`~.client.DBLClient`)
            An instance of DBLClient.
    """

    __slots__ = (
        "_error",
        "_success",
        "_interval",
        "_task",
        "client",
        "_stats",
        "_stopping",
    )

    _success: CallbackT
    _stats: CallbackT
    _interval: float
    _task: t.Optional["asyncio.Task[None]"]

    def __init__(self, client: "DBLClient") -> None:
        super().__init__()
        self.client = client
        self._interval: float = 900
        self._error = self._default_error_handler
        self._refresh_state()

    def _default_error_handler(self, exception: Exception) -> None:
        print("Ignoring exception in auto post loop:", file=sys.stderr)
        traceback.print_exception(type(exception), exception, exception.__traceback__, file=sys.stderr)

    @t.overload
    def on_success(self, callback: None) -> t.Callable[[CallbackT], CallbackT]: ...

    @t.overload
    def on_success(self, callback: CallbackT) -> "AutoPoster": ...

    def on_success(self, callback: t.Any = None) -> t.Any:
        """
        Registers an autopost success callback. The callback can be either sync or async.

        The callback is not required to take in arguments, but you can have injected :obj:`~.data.data`.
        This method can be used as a decorator or a decorator factory.

        :Example:
            .. code-block:: python

                # The following are valid.
                autopost = dblclient.autopost().on_success(lambda: print("Success!"))


                # Used as decorator, the decorated function will become the AutoPoster object.
                @autopost.on_success
                def autopost(): ...


                # Used as decorator factory, the decorated function will still be the function itself.
                @autopost.on_success()
                def on_success(): ...
        """
        if callback is not None:
            self._success = callback
            return self

        def decorator(callback: CallbackT) -> CallbackT:
            self._success = callback
            return callback

        return decorator

    @t.overload
    def on_error(self, callback: None) -> t.Callable[[CallbackT], CallbackT]: ...

    @t.overload
    def on_error(self, callback: CallbackT) -> "AutoPoster": ...

    def on_error(self, callback: t.Any = None) -> t.Any:
        """
        Registers an autopost error callback. The callback can be either sync or async.

        The callback is expected to take in the exception being raised, you can also
        have injected :obj:`~.data.data`.
        This method can be used as a decorator or a decorator factory.

        Note:
            If you don't provide an error callback, the default error handler will be called.

        :Example:
            .. code-block:: python

                # The following are valid.
                autopost = dblclient.autopost().on_error(lambda exc: print("Failed posting stats!", exc))


                # Used as decorator, the decorated function will become the AutoPoster object.
                @autopost.on_error
                def autopost(exc: Exception): ...


                # Used as decorator factory, the decorated function will still be the function itself.
                @autopost.on_error()
                def on_error(exc: Exception): ...
        """
        if callback is not None:
            self._error = callback
            return self

        def decorator(callback: CallbackT) -> CallbackT:
            self._error = callback
            return callback

        return decorator

    @t.overload
    def stats(self, callback: None) -> t.Callable[[StatsCallbackT], StatsCallbackT]: ...

    @t.overload
    def stats(self, callback: StatsCallbackT) -> "AutoPoster": ...

    def stats(self, callback: t.Any = None) -> t.Any:
        """
        Registers a function that returns an instance of :obj:`~.types.StatsWrapper`.

        The callback can be either sync or async.
        The callback is not required to take in arguments, but you can have injected :obj:`~.data.data`.
        This method can be used as a decorator or a decorator factory.

        :Example:
            .. code-block:: python

                import topgg

                # In this example, we fetch the stats from a Discord client instance.
                client = Client(...)
                dblclient = topgg.DBLClient(TOKEN).set_data(client)
                autopost = dblclient.autopost().on_success(lambda: print("Successfully posted the stats!"))


                @autopost.stats()
                def get_stats(client: Client = topgg.data(Client)):
                    return topgg.StatsWrapper(guild_count=len(client.guilds), shard_count=len(client.shards))


                # somewhere after the event loop has started
                autopost.start()
        """
        if callback is not None:
            self._stats = callback
            return self

        def decorator(callback: StatsCallbackT) -> StatsCallbackT:
            self._stats = callback
            return callback

        return decorator

    @property
    def interval(self) -> float:
        """The interval between posting stats."""
        return self._interval

    @interval.setter
    def interval(self, seconds: t.Union[float, datetime.timedelta]) -> None:
        """Alias to :meth:`~.autopost.AutoPoster.set_interval`."""
        self.set_interval(seconds)

    def set_interval(self, seconds: t.Union[float, datetime.timedelta]) -> "AutoPoster":
        """
        Sets the interval between posting stats.

        Args:
            seconds (Union[:obj:`float`, :obj:`datetime.timedelta`])
                The interval.

        Raises:
            ValueError
                If the provided interval is less than 900 seconds.
        """
        if isinstance(seconds, datetime.timedelta):
            seconds = seconds.total_seconds()

        if seconds < 900:
            raise ValueError("interval must be greated than 900 seconds.")

        self._interval = seconds
        return self

    @property
    def is_running(self) -> bool:
        """Whether or not the autopost is running."""
        return self._task is not None and not self._task.done()

    def _refresh_state(self) -> None:
        self._task = None
        self._stopping = False

    def _fut_done_callback(self, future: "asyncio.Future") -> None:
        self._refresh_state()
        if future.cancelled():
            return
        future.exception()

    async def _internal_loop(self) -> None:
        try:
            while 1:
                stats = await self.client._invoke_callback(self._stats)
                try:
                    await self.client.post_guild_count(stats)
                except Exception as err:
                    await self.client._invoke_callback(self._error, err)
                    if isinstance(err, errors.Unauthorized):
                        raise err from None
                else:
                    on_success = getattr(self, "_success", None)
                    if on_success:
                        await self.client._invoke_callback(on_success)

                if self._stopping:
                    return None

                await asyncio.sleep(self.interval)
        finally:
            self._refresh_state()

    def start(self) -> "asyncio.Task[None]":
        """
        Starts the autoposting loop.

        Note:
            This method must be called when the event loop has already running!

        Raises:
            :exc:`~.errors.TopGGException`
                If there's no callback provided or the autopost is already running.
        """
        if not hasattr(self, "_stats"):
            raise errors.TopGGException("you must provide a callback that returns the stats.")

        if self.is_running:
            raise errors.TopGGException("the autopost is already running.")

        self._task = task = asyncio.ensure_future(self._internal_loop())
        task.add_done_callback(self._fut_done_callback)
        return task

    def stop(self) -> None:
        """
        Stops the autoposting loop.

        Note:
            This differs from :meth:`~.autopost.AutoPoster.cancel`
            because this will post once before stopping as opposed to cancel immediately.
        """
        if not self.is_running:
            return None

        self._stopping = True

    def cancel(self) -> None:
        """
        Cancels the autoposting loop.

        Note:
            This differs from :meth:`~.autopost.AutoPoster.stop`
            because this will stop the loop right away.
        """
        if self._task is None:
            return

        self._task.cancel()
        self._refresh_state()
        return None
