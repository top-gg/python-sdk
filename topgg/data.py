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

__all__ = ["data", "DataContainerMixin"]

import inspect
import typing as t

from topgg.errors import TopGGException

T = t.TypeVar("T")
DataContainerT = t.TypeVar("DataContainerT", bound="DataContainerMixin")


# this is meant to be a singleton,
# but we don't care if it's instantiated more than once
# we'll only use the one we instantiated here: _UNSET.
class _UnsetType:
    def __bool__(self) -> bool:
        return False


_UNSET = _UnsetType()


def data(type_: t.Type[T]) -> T:
    """
    Represents the injected data. This should be set as the parameter's default value.

    Args:
        `type_` (:obj:`type` [ :obj:`T` ])
            The type of the injected data.

    Returns:
        :obj:`T`: The injected data of type T.

    :Example:
        .. code-block:: python

            import topgg

            # In this example, we fetch the stats from a Discord client instance.
            client = Client(...)
            dblclient = topgg.DBLClient(TOKEN).set_data(client)
            autopost: topgg.AutoPoster = dblclient.autopost()

            @autopost.stats()
            def get_stats(client: Client = topgg.data(Client)):
                return topgg.StatsWrapper(guild_count=len(client.guilds), shard_count=len(client.shards))
    """
    return t.cast(T, Data(type_))


class Data(t.Generic[T]):
    __slots__ = ("type",)

    def __init__(self, type_: t.Type[T]) -> None:
        self.type: t.Type[T] = type_


class DataContainerMixin:
    """
    A class that holds data.

    This is useful for injecting some data so that they're available
    as arguments in your functions.
    """

    __slots__ = ("_data", "_lookup_cache")

    def __init__(self) -> None:
        self._data: t.Dict[t.Type, t.Any] = {type(self): self}
        self._lookup_cache: t.Dict[t.Type, t.Any] = {}

    def set_data(
        self: DataContainerT, data_: t.Any, *, override: bool = False
    ) -> DataContainerT:
        """
        Sets data to be available in your functions.

        Args:
            `data_` (:obj:`typing.Any`)
                The data to be injected.
            override (:obj:`bool`)
                Whether or not to override another instance that already exists.

        Raises:
            :obj:`~.errors.TopGGException`
                If override is False and another instance of the same type exists.
        """
        type_ = type(data_)
        if not override and type_ in self._data:
            raise TopGGException(
                f"{type_} already exists. If you wish to override it, pass True into the override parameter."
            )

        # exclude the type itself and object
        for sup in type_.mro()[1:-1]:
            if sup in self._lookup_cache:
                self._lookup_cache[sup] = data_

        self._data[type_] = data_
        return self

    @t.overload
    def get_data(self, type_: t.Type[T]) -> t.Optional[T]:
        ...

    @t.overload
    def get_data(self, type_: t.Type[T], default: t.Any = None) -> t.Any:
        ...

    def get_data(self, type_: t.Any, default: t.Any = None) -> t.Any:
        """Gets the injected data."""
        try:
            return self._get_data(type_)
        except LookupError:
            return default

    async def _invoke_callback(
        self, callback: t.Callable[..., T], *args: t.Any, **kwargs: t.Any
    ) -> T:
        parameters: t.Mapping[str, inspect.Parameter]
        try:
            parameters = inspect.signature(callback).parameters
        except (ValueError, TypeError):
            parameters = {}

        signatures: t.Dict[str, Data] = {
            k: v.default
            for k, v in parameters.items()
            if v.kind is inspect.Parameter.POSITIONAL_OR_KEYWORD
            and isinstance(v.default, Data)
        }

        for k, v in signatures.items():
            signatures[k] = self._get_data(v.type)

        res = callback(*args, **{**signatures, **kwargs})
        if inspect.isawaitable(res):
            return await res

        return res

    def _resolve_data(self, type_: t.Type[T]) -> t.Union[_UnsetType, t.Tuple[bool, T]]:
        maybe_data = self._data.get(type_, _UNSET)
        if maybe_data is not _UNSET:
            return False, maybe_data

        cache = self._lookup_cache.get(type_, _UNSET)
        if cache is not _UNSET:
            return False, cache

        for subclass in type_.__subclasses__():
            maybe_data = self._resolve_data(subclass)
            if maybe_data is not _UNSET:
                return True, maybe_data[1]

        return _UNSET

    def _get_data(self, type_: t.Type[T]) -> T:
        maybe_data = self._resolve_data(type_)
        if maybe_data is _UNSET:
            raise LookupError(f"data of type {type_} can't be found.")

        assert isinstance(maybe_data, tuple)
        is_subclass, data = maybe_data
        if is_subclass:
            self._lookup_cache[type_] = data

        return data
