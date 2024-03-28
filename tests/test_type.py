import pytest

from topgg import types

d: dict = {
    "defAvatar": "6debd47ed13483642cf09e832ed0bc1b",
    "invite": "",
    "website": "https://top.gg",
    "support": "KYZsaFb",
    "github": "https://github.com/top-gg/Luca",
    "longdesc": "Luca only works in the **Discord Bot List** server.    \nPrepend commands with the prefix `-` or "
    "`@Luca#1375`.    \n**Please refrain from using these commands in non testing channels.**\n- `botinfo "
    "@bot` Shows bot info, title redirects to site listing.\n- `bots @user`* Shows all bots of that user, "
    "includes bots in the queue.\n- `owner / -owners @bot`* Shows all owners of that bot.\n- `prefix "
    "@bot`* Shows the prefix of that bot.\n* Mobile friendly version exists. Just add `noembed` to the "
    "end of the command.\n",
    "shortdesc": "Luca is a bot for managing and informing members of the server",
    "prefix": "- or @Luca#1375",
    "lib": None,
    "clientid": "264811613708746752",
    "avatar": "7edcc4c6fbb0b23762455ca139f0e1c9",
    "id": "264811613708746752",
    "discriminator": "1375",
    "username": "Luca",
    "date": "2017-04-26T18:08:17.125Z",
    "server_count": 2,
    "guilds": ["417723229721853963", "264445053596991498"],
    "shards": [],
    "monthlyPoints": 19,
    "points": 397,
    "certifiedBot": False,
    "owners": ["129908908096487424"],
    "tags": ["Moderation", "Role Management", "Logging"],
    "donatebotguildid": "",
}

query_dict = {"qwe": "1", "rty": "2", "uio": "3"}

vote_data_dict = {
    "type": "test",
    "query": "?" + "&".join(f"{k}={v}" for k, v in query_dict.items()),
    "user": "1",
}

bot_vote_dict = {
    "bot": "2",
    "user": "3",
    "type": "test",
    "query": "?" + "&".join(f"{k}={v}" for k, v in query_dict.items()),
}

server_vote_dict = {
    "guild": "4",
    "user": "5",
    "type": "upvote",
    "query": "?" + "&".join(f"{k}={v}" for k, v in query_dict.items()),
}

user_data_dict = {
    "discriminator": "0001",
    "avatar": "a_1241439d430def25c100dd28add2d42f",
    "id": "140862798832861184",
    "username": "Xetera",
    "defAvatar": "322c936a8c8be1b803cd94861bdfa868",
    "admin": True,
    "webMod": True,
    "mod": True,
    "certifiedDev": False,
    "supporter": False,
    "social": {},
}

bot_stats_dict = {"shards": [1, 5, 8]}


@pytest.fixture
def data_dict() -> types.DataDict:
    return types.DataDict(**d)


@pytest.fixture
def bot_data() -> types.BotData:
    return types.BotData(**d)


@pytest.fixture
def user_data() -> types.UserData:
    return types.UserData(**user_data_dict)


@pytest.fixture
def widget_options() -> types.WidgetOptions:
    return types.WidgetOptions(id=int(d["id"]))


@pytest.fixture
def vote_data() -> types.VoteDataDict:
    return types.VoteDataDict(**vote_data_dict)


@pytest.fixture
def bot_vote_data() -> types.BotVoteData:
    return types.BotVoteData(**bot_vote_dict)


@pytest.fixture
def server_vote_data() -> types.GuildVoteData:
    return types.GuildVoteData(**server_vote_dict)


@pytest.fixture
def bot_stats_data() -> types.BotStatsData:
    return types.BotStatsData(**bot_stats_dict)


def test_data_dict_fields(data_dict: types.DataDict) -> None:
    for attr in data_dict:
        if "id" in attr.lower():
            assert isinstance(data_dict[attr], int) or data_dict[attr] is None
        assert data_dict.get(attr) == data_dict[attr] == getattr(data_dict, attr)


def test_bot_data_fields(bot_data: types.BotData) -> None:
    bot_data.github = "I'm a GitHub link!"
    bot_data.support = "Support has arrived!"

    for attr in bot_data:
        if "id" in attr.lower():
            assert isinstance(bot_data[attr], int) or bot_data[attr] is None
        elif attr in ("owners", "guilds"):
            for item in bot_data[attr]:
                assert isinstance(item, int)
        assert bot_data.get(attr) == bot_data[attr] == getattr(bot_data, attr)


def test_widget_options_fields(widget_options: types.WidgetOptions) -> None:
    assert widget_options["colors"] == widget_options["colours"]

    widget_options.colours = {"background": 0}
    widget_options["colours"]["text"] = 255
    assert widget_options.colours == widget_options["colors"]

    for attr in widget_options:
        if "id" in attr.lower():
            assert isinstance(widget_options[attr], int) or widget_options[attr] is None
        assert widget_options.get(attr) == widget_options[attr] == widget_options[attr] == getattr(widget_options, attr)


def test_vote_data_fields(vote_data: types.VoteDataDict) -> None:
    assert isinstance(vote_data.query, dict)
    vote_data.type = "upvote"

    for attr in vote_data:
        assert getattr(vote_data, attr) == vote_data.get(attr) == vote_data[attr]


def test_bot_vote_data_fields(bot_vote_data: types.BotVoteData) -> None:
    assert isinstance(bot_vote_data.query, dict)
    bot_vote_data.type = "upvote"

    assert isinstance(bot_vote_data["bot"], int)
    for attr in bot_vote_data:
        assert getattr(bot_vote_data, attr) == bot_vote_data.get(attr) == bot_vote_data[attr]


def test_server_vote_data_fields(server_vote_data: types.BotVoteData) -> None:
    assert isinstance(server_vote_data.query, dict)
    server_vote_data.type = "upvote"

    assert isinstance(server_vote_data["guild"], int)
    for attr in server_vote_data:
        assert getattr(server_vote_data, attr) == server_vote_data.get(attr) == server_vote_data[attr]


def test_bot_stats_data_attrs(bot_stats_data: types.BotStatsData) -> None:
    for count in ("server_count", "shard_count"):
        assert isinstance(bot_stats_data[count], int) or bot_stats_data[count] is None
    assert isinstance(bot_stats_data.shards, list)
    if bot_stats_data.shards:
        for shard in bot_stats_data.shards:
            assert isinstance(shard, int)


def test_user_data_attrs(user_data: types.UserData) -> None:
    assert isinstance(user_data.social, types.SocialData)
    for attr in user_data:
        if "id" in attr.lower():
            assert isinstance(user_data[attr], int) or user_data[attr] is None
        assert user_data[attr] == getattr(user_data, attr) == user_data.get(attr)
