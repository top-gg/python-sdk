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

__all__ = [
    "endpoint",
    "BoundWebhookEndpoint",
    "WebhookEndpoint",
    "WebhookManager",
    "WebhookType",
]

import enum
import typing as t

import aiohttp
from aiohttp import web

from topgg.errors import TopGGException

from .data import DataContainerMixin
from .types import BotVoteData, GuildVoteData

if t.TYPE_CHECKING:
    from aiohttp.web import Request, StreamResponse

T = t.TypeVar("T", bound="WebhookEndpoint")
_HandlerT = t.Callable[["Request"], t.Awaitable["StreamResponse"]]


class WebhookType(enum.Enum):
    """An enum that represents the type of an endpoint."""

    BOT = enum.auto()
    """Marks the endpoint as a bot webhook."""

    GUILD = enum.auto()
    """Marks the endpoint as a guild webhook."""


class WebhookManager(DataContainerMixin):
    """
    A class for managing Top.gg webhooks.
    """

    __app: web.Application
    _webserver: web.TCPSite
    _is_closed: bool
    __slots__ = ("__app", "_webserver", "_is_running")

    def __init__(self) -> None:
        super().__init__()
        self.__app = web.Application()
        self._is_running = False

    @t.overload
    def endpoint(self, endpoint_: None = None) -> "BoundWebhookEndpoint": ...

    @t.overload
    def endpoint(self, endpoint_: "WebhookEndpoint") -> "WebhookManager": ...

    def endpoint(self, endpoint_: t.Optional["WebhookEndpoint"] = None) -> t.Any:
        """Helper method that returns a WebhookEndpoint object.

        Args:
            `endpoint_` (Optional[:obj:`WebhookEndpoint`])
                The endpoint to add.

        Returns:
            Union[:obj:`WebhookManager`, :obj:`BoundWebhookEndpoint`]:
                An instance of :obj:`WebhookManager` if endpoint was provided,
                otherwise :obj:`BoundWebhookEndpoint`.

        Raises:
            :exc:`~.errors.TopGGException`
                If the endpoint is lacking attributes.
        """
        if endpoint_:
            if not hasattr(endpoint_, "_callback"):
                raise TopGGException("endpoint missing callback.")

            if not hasattr(endpoint_, "_type"):
                raise TopGGException("endpoint missing type.")

            if not hasattr(endpoint_, "_route"):
                raise TopGGException("endpoint missing route.")

            self.app.router.add_post(
                endpoint_._route,
                self._get_handler(endpoint_._type, endpoint_._auth, endpoint_._callback),
            )
            return self

        return BoundWebhookEndpoint(manager=self)

    async def start(self, port: int) -> None:
        """Runs the webhook.

        Args:
            port (int)
                The port to run the webhook on.
        """
        runner = web.AppRunner(self.__app)
        await runner.setup()
        self._webserver = web.TCPSite(runner, "0.0.0.0", port)
        await self._webserver.start()
        self._is_running = True

    @property
    def is_running(self) -> bool:
        """Returns whether or not the webserver is running."""
        return self._is_running

    @property
    def app(self) -> web.Application:
        """Returns the internal web application that handles webhook requests.

        Returns:
            :class:`aiohttp.web.Application`:
                The internal web application.
        """
        return self.__app

    async def close(self) -> None:
        """Stops the webhook."""
        await self._webserver.stop()
        self._is_running = False

    def _get_handler(self, type_: WebhookType, auth: str, callback: t.Callable[..., t.Any]) -> _HandlerT:
        async def _handler(request: aiohttp.web.Request) -> web.Response:
            if request.headers.get("Authorization", "") != auth:
                return web.Response(status=401, text="Unauthorized")

            data = await request.json()
            await self._invoke_callback(
                callback,
                (BotVoteData if type_ is WebhookType.BOT else GuildVoteData)(**data),
            )
            return web.Response(status=200, text="OK")

        return _handler


CallbackT = t.Callable[..., t.Any]


class WebhookEndpoint:
    """
    A helper class to setup webhook endpoint.
    """

    __slots__ = ("_callback", "_auth", "_route", "_type")

    def __init__(self) -> None:
        self._auth = ""

    def __call__(self, *args: t.Any, **kwargs: t.Any) -> t.Any:
        return self._callback(*args, **kwargs)

    def type(self: T, type_: WebhookType) -> T:
        """Sets the type of this endpoint.

        Args:
            `type_` (:obj:`WebhookType`)
                The type of the endpoint.

        Returns:
            :obj:`WebhookEndpoint`
        """
        self._type = type_
        return self

    def route(self: T, route_: str) -> T:
        """
        Sets the route of this endpoint.

        Args:
            `route_` (str)
                The route of this endpoint.

        Returns:
            :obj:`WebhookEndpoint`
        """
        self._route = route_
        return self

    def auth(self: T, auth_: str) -> T:
        """
        Sets the auth of this endpoint.

        Args:
            `auth_` (str)
                The auth of this endpoint.

        Returns:
            :obj:`WebhookEndpoint`
        """
        self._auth = auth_
        return self

    @t.overload
    def callback(self, callback_: None) -> t.Callable[[CallbackT], CallbackT]: ...

    @t.overload
    def callback(self: T, callback_: CallbackT) -> T: ...

    def callback(self, callback_: t.Any = None) -> t.Any:
        """
        Registers a vote callback, called whenever this endpoint receives POST requests.

        The callback can be either sync or async.
        This method can be used as a decorator or a decorator factory.

        :Example:
            .. code-block:: python

                import topgg

                webhook_manager = topgg.WebhookManager()
                endpoint = topgg.WebhookEndpoint().type(topgg.WebhookType.BOT).route("/dblwebhook").auth("youshallnotpass")

                # The following are valid.
                endpoint.callback(lambda vote_data: print("Receives a vote!", vote_data))


                # Used as decorator, the decorated function will become the WebhookEndpoint object.
                @endpoint.callback
                def endpoint(vote_data: topgg.BotVoteData): ...


                # Used as decorator factory, the decorated function will still be the function itself.
                @endpoint.callback()
                def on_vote(vote_data: topgg.BotVoteData): ...


                webhook_manager.endpoint(endpoint)
        """
        if callback_ is not None:
            self._callback = callback_
            return self

        return self.callback


class BoundWebhookEndpoint(WebhookEndpoint):
    """
    A WebhookEndpoint with a WebhookManager bound to it.

    You can instantiate this object using the :meth:`WebhookManager.endpoint` method.

    :Example:
        .. code-block:: python

            import topgg

            webhook_manager = (
                topgg.WebhookManager().endpoint().type(topgg.WebhookType.BOT).route("/dblwebhook").auth("youshallnotpass")
            )

            # The following are valid.
            endpoint.callback(lambda vote_data: print("Receives a vote!", vote_data))


            # Used as decorator, the decorated function will become the BoundWebhookEndpoint object.
            @endpoint.callback
            def endpoint(vote_data: topgg.BotVoteData): ...


            # Used as decorator factory, the decorated function will still be the function itself.
            @endpoint.callback()
            def on_vote(vote_data: topgg.BotVoteData): ...


            endpoint.add_to_manager()
    """

    __slots__ = ("manager",)

    def __init__(self, manager: WebhookManager):
        super().__init__()
        self.manager = manager

    def add_to_manager(self) -> WebhookManager:
        """
        Adds this endpoint to the webhook manager.

        Returns:
            :obj:`WebhookManager`

        Raises:
            :obj:`errors.TopGGException`:
                If the object lacks attributes.
        """
        self.manager.endpoint(self)
        return self.manager


def endpoint(route: str, type: WebhookType, auth: str = "") -> t.Callable[[t.Callable[..., t.Any]], WebhookEndpoint]:
    """
    A decorator factory for instantiating WebhookEndpoint.

    Args:
        route (str)
            The route for the endpoint.
        type (WebhookType)
            The type of the endpoint.
        auth (str)
            The auth for the endpoint.

    Returns:
        Callable[[Callable[..., Any]], :obj:`WebhookEndpoint`]:
            The actual decorator.

    :Example:
        .. code-block:: python

            import topgg


            @topgg.endpoint("/dblwebhook", WebhookType.BOT, "youshallnotpass")
            async def on_vote(
                vote_data: topgg.BotVoteData,
                # database here is an injected data
                database: Database = topgg.data(Database),
            ): ...
    """

    def decorator(func: t.Callable[..., t.Any]) -> WebhookEndpoint:
        return WebhookEndpoint().route(route).type(type).auth(auth).callback(func)

    return decorator
