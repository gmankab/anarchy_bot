# license is gnu agpl 3 - gnu.org/licenses/agpl-3.0.en.html

import pyrogram as pg
import pyrogram.errors
from lang import t
from pyrogram.client import Client
from pyrogram.types import (
    Message,
)
from bot import (
    becomeadmin,
    mute,
)
from config import(
    yes_no,
    config,
)
from common import (
    IgnoreError,
    filter_admin,
    write_error,
    get_buttons,
    chats,
    l,
)
from chats import (
    ask_to_set_logs_chat_msg,
    notify_removed,
    setlogs_msg,
)


async def catched_on_message(
    client: Client,
    msg: Message,
):
    try:
        await on_message(
            client,
            msg,
        )
    except pyrogram.errors.FloodWait as e:
        print(f'got fooldwait for {e.value} seconds')
        return
    except IgnoreError:
        return
    except Exception:
        error_path = write_error()
        log_msg = await l.log(
            file = error_path
        )
        if not log_msg:
            log_msg = error_path
        await msg.reply(
            f'unknown error, please forward this message to @gmankachat\n\nlog: {log_msg}'
        )


def is_command(
    msg_text: str,
    command: str,
) -> bool:
    if msg_text == command:
        return True
    if msg_text.startswith(command + ' '):
        return True
    if msg_text.startswith(f'{command}@{config.me.username}'):
        return True
    return False


async def on_message(
    client: Client,
    msg: Message,
) -> None:
    users = {
        '/h': help_msg,
        '/help': help_msg,
        '/becomeadmin': becomeadmin,
        '/ba': becomeadmin,
        '/m': mute,
        '/mute': mute,
    }
    admins = {
        '/setlogs': setlogs_msg,
    }
    if msg.service:
        if msg.service == pg.enums.MessageServiceType.LEFT_CHAT_MEMBERS:
            await notify_removed(msg)
        return
    if not msg.text:
        return
    if msg.chat.type == pg.enums.ChatType.PRIVATE:
        if not config.owner:
            await set_owner(
                msg,
            )
        await chats.remember_user(msg.from_user.id)
        action = chats.users_dict[msg.from_user.id]
        if action is None:
            pass
    else:
        await chats.remember_chat(
            client,
            msg.chat,
        )
        start = {
            'logs': ask_to_set_logs_chat_msg,
        }
        for action, to_run in start.items():
            if msg.text.endswith('?startgroup=' + action):
                await to_run(client, msg)
                return
    for excpected_msg, to_run in users.items():
        if is_command(
            msg.text,
            excpected_msg,
        ):
            return await to_run(client, msg)
    for excpected_msg, to_run in admins.items():
        if is_command(
            msg.text,
            excpected_msg,
        ):
            if await filter_admin(msg):
                return
            return await to_run(client, msg)
    if msg.chat.type == pg.enums.ChatType.PRIVATE:
        await help_msg(
            client,
            msg,
        )
        return


async def help_msg(
    _: Client,
    msg: Message,
):
    await msg.reply(
        t('help_msg', msg),
        disable_web_page_preview = True,
    )
    if msg.from_user.id not in config.admins:
        return
    await msg.reply(
        text = t('owner_commands_msg', msg),
        reply_markup = get_buttons(
        [['admin_panel_button']],
        msg,
    )
,
    )

async def set_owner(
    msg: Message,
) -> None:
    await msg.reply(
        t('setup_msg', msg).format(
            username = config.me.username
        )
    )
    user = msg.from_user
    if yes_no(
        f'''
you have not added an admin yet

this user contacted bot:

username - @{user.username}
name - {user.first_name}
id - {user.id}

do you want to make him admin? [Y/n] \
'''
    ):
        config.owner = user.id
        if config.owner not in config.admins:
            config.admins.append(user.id)
        config.to_disk()
        await l.notify(f'success: new admin {user.id}')
    else:
        await l.log(f'canceled adding {user.id} to admins')
        await msg.reply(f'canceled adding {user.id} to admins')

