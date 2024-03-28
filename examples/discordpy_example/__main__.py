# The MIT License (MIT)

# Copyright (c) 2021 Norizon
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
import discord

import topgg

from .callbacks import autopost, webhook

client = discord.Client()
webhook_manager = topgg.WebhookManager().set_data(client).endpoint(webhook.endpoint)
dblclient = topgg.DBLClient("TOPGG_TOKEN").set_data(client)
autoposter: topgg.AutoPoster = (
    dblclient.autopost()
    .on_success(autopost.on_autopost_success)
    .on_error(autopost.on_autopost_error)
    .stats(autopost.stats)
)


@client.event
async def on_ready():
    assert client.user is not None

    # if it's ready, then the event loop's run,
    # hence it's safe starting the autopost here
    if not autoposter.is_running:
        # don't await unless you want to wait for the autopost loop to get finished
        autoposter.start()

    # we can also start the webhook here
    if not webhook_manager.is_running:
        await webhook_manager.start(6000)


# TODO: find a way to figure out when the bot shuts down
# so we can close the client and the webhook manager

client.run("TOKEN")
