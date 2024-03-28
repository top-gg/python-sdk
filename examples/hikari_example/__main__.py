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
import hikari

import topgg

from .callbacks import autopost, webhook

app = hikari.GatewayBot("TOKEN")
webhook_manager = topgg.WebhookManager().set_data(app).endpoint(webhook.endpoint)
dblclient = topgg.DBLClient("TOPGG_TOKEN").set_data(app)
autoposter: topgg.AutoPoster = (
    dblclient.autopost()
    .on_success(autopost.on_autopost_success)
    .on_error(autopost.on_autopost_error)
    .stats(autopost.stats)
)


@app.listen()
async def on_started(event: hikari.StartedEvent):
    me: hikari.OwnUser = event.app.get_me()
    assert me is not None

    # since StartedEvent is a lifetime event
    # this event will only get dispatched once
    autoposter.start()
    await webhook_manager.start(6000)


@app.listen()
async def on_stopping(_: hikari.StoppingEvent):
    await dblclient.close()
    await webhook_manager.close()


app.run()
