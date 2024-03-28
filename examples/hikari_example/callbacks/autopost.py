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
import logging

import hikari

import topgg

# from ..events.autopost import AutoPostErrorEvent, AutoPostSuccessEvent

_LOGGER = logging.getLogger("callbacks.autopost")


# these functions can be async too!
def on_autopost_success(
    # uncomment this if you want to get access to app
    # app: hikari.GatewayBot = topgg.data(hikari.GatewayBot),
):
    # will be called whenever it successfully posting
    _LOGGER.info("Successfully posted!")

    # do whatever with app
    # you can dispatch your own event for more callbacks
    # app.dispatch(AutoPostSuccessEvent(app=app))


def on_autopost_error(
    exception: Exception,
    # uncomment this if you want to get access to app
    # app: hikari.GatewayBot = topgg.data(hikari.GatewayBot),
):
    # will be called whenever it failed posting
    _LOGGER.error("Failed to post...", exc_info=exception)

    # do whatever with app
    # you can dispatch your own event for more callbacks
    # app.dispatch(AutoPostErrorEvent(app=app, exception=exception))


def stats(app: hikari.GatewayBot = topgg.data(hikari.GatewayBot)):
    return topgg.StatsWrapper(guild_count=len(app.cache.get_guilds_view()), shard_count=app.shard_count)
