# license is gnu agpl 3 - gnu.org/licenses/agpl-3.0.en.html

try:
    import uvloop
    uvloop.install()
except Exception:
    pass

import sys
import signal
import asyncio
from cb import catched_on_cb
from msg import catched_on_message
from inline import catched_on_inline
from contextlib import suppress
from pyrogram.client import Client
from pyrogram.handlers.message_handler import MessageHandler
from pyrogram.handlers.inline_query_handler import InlineQueryHandler
from pyrogram.handlers.callback_query_handler import CallbackQueryHandler
from config import (
    interactive_input,
    start_message,
    app_name,
    config,
    c,
)
from common import (
    write_error,
    l,
)


async def idle():
    while True:
        await asyncio.sleep(1)


async def main():
    while True:
        if not config.session:
            if not config.token:
                config.token = interactive_input(
                    f'please input bot token: ',
                )
                config.to_disk()
            client =  Client(
                name = app_name,
                api_id = 1,   
                api_hash = 'b6b154c3707471f5339bd661645ed3d6',
                bot_token = config.token,
                in_memory = True,
            )
            try:
                await client.start()
                config.session = str(
                    await client.export_session_string()
                )
                await config.init(client = client)
            except:
                c.log(f'[red]error:[/red] bad token {write_error()}')
                config.token = None
                continue
            config.to_disk()
            break
        client = Client(
            name = app_name,
            session_string = config.session
        )
        try:
            await client.start()
            await config.init(client = client)
        except:
            c.log(f'[red]error:[/red] bad session {write_error()}')
            config.session = ''
            continue
        break
    await l.init(client = client)
    await l.log(start_message)
    for handler, to_call in {
        MessageHandler: catched_on_message,
        CallbackQueryHandler: catched_on_cb,
        InlineQueryHandler: catched_on_inline,
    }.items():
        client.add_handler(
            handler(
                to_call
            )
        )
    await idle()


if __name__ == 'main':
    try:
        loop = asyncio.get_event_loop()
        loop.add_signal_handler(
            signal.SIGINT,
            loop.stop,
        )
        loop.run_until_complete(
            main()
        )
        for task in asyncio.all_tasks(loop):
            task.cancel()
        with suppress(
            asyncio.CancelledError
        ):
            loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()
    except (
        KeyboardInterrupt,
        RuntimeError,
    ):
        print(' exiting')
        sys.exit()

