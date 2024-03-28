import pytest

from topgg.data import DataContainerMixin, data
from topgg.errors import TopGGException


@pytest.fixture
def data_container() -> DataContainerMixin:
    dc = DataContainerMixin()
    dc.set_data("TEXT")
    dc.set_data(200)
    dc.set_data({"a": "b"})
    return dc


async def _async_callback(text: str = data(str), number: int = data(int), mapping: dict = data(dict)): ...


def _sync_callback(text: str = data(str), number: int = data(int), mapping: dict = data(dict)): ...


def _invalid_callback(number: float = data(float)): ...


@pytest.mark.asyncio
async def test_data_container_invoke_async_callback(data_container: DataContainerMixin):
    await data_container._invoke_callback(_async_callback)


@pytest.mark.asyncio
async def test_data_container_invoke_sync_callback(data_container: DataContainerMixin):
    await data_container._invoke_callback(_sync_callback)


def test_data_container_raises_data_already_exists(data_container: DataContainerMixin):
    with pytest.raises(
        TopGGException,
        match="<class 'str'> already exists. If you wish to override it, " "pass True into the override parameter.",
    ):
        data_container.set_data("TEST")


@pytest.mark.asyncio
async def test_data_container_raises_key_error(data_container: DataContainerMixin):
    with pytest.raises(KeyError):
        await data_container._invoke_callback(_invalid_callback)


def test_data_container_get_data(data_container: DataContainerMixin):
    assert data_container.get_data(str) == "TEXT"
    assert data_container.get_data(float) is None
    assert isinstance(data_container.get_data(set, set()), set)
