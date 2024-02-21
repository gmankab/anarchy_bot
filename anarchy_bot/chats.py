# license is gnu agpl 3 - gnu.org/licenses/agpl-3.0.en.html

import pyrogram as pg
from lang import t
from pyrogram.client import Client
from pyrogram.types import (
    InlineKeyboardButton as Ikb,
    InlineKeyboardMarkup as Ikm,
    CallbackQuery,
    Message,
)
from config import (
    config,
    c,
)
from common import (
    get_buttons,
    mention,
    url,
    l,
)


async def ask_to_set_logs_chat_msg(
    client: Client,
    msg: Message,
):
    if msg.from_user.id not in config.admins:
        await msg.reply(t('denied', msg))
        return
    if l.logs_chat and msg.chat.id == l.logs_chat.id:
        await msg.reply('already using this chat for logs')
        return
    done_button = t('done_button', msg)
    if msg.chat.type != pg.enums.ChatType.SUPERGROUP:
        await client.send_message(
            chat_id = msg.chat.id,
            text = f'''
to use this chat as logs chat, you must convert it to supergroup

1) open chat settings
2) enable topics
3) open chat settings again and disable topics
4) press {done_button}
''',
            reply_markup = Ikm([[Ikb(
                text = done_button,
                callback_data = f'confirm_set_logs_chat_button',
            )]])
        )
        return True
    await client.send_message(
        chat_id = msg.chat.id,
        text = t('ask_to_set_logs_chat_msg', msg).format(
            title = msg.chat.title,
        ),
        reply_markup = get_buttons(
            [['confirm_set_logs_chat_button']],
            msg,
        ),
    )
    return


async def setlogs_msg(
    client: Client,
    msg: Message,
):
    if msg.chat.type != pg.enums.ChatType.SUPERGROUP:
        await msg.reply(
            'wrong chat type, expected supergroup, got ' + str(msg.chat.type).lower()
        )
        return
    await l.init(
        client = client,
        logs_chat = msg.chat,
    )
    await l.notify(
        text = f'{mention(msg.from_user)} set new logs chat',
        reply_markup = Ikm([
            [Ikb(
                t('open_logs_chat_button', msg),
                url = url(msg.chat.id),
            )],
            [Ikb(
                t('main_menu_button', msg),
                'main_menu_button',
            )],
        ])
    )


async def confirm_set_logs_chat_button(
    client: Client,
    cb: CallbackQuery,
) -> None:
    if cb.message.chat.type != pg.enums.ChatType.SUPERGROUP:
        await cb.answer(
            'wrong chat type, expected supergroup, got ' + str(cb.message.chat.type).lower()
        )
        return
    await l.init(
        client = client,
        logs_chat = cb.message.chat,
    )
    await l.notify(
        text = f'{mention(cb.from_user)} set new logs chat',
        reply_markup = Ikm([
            [Ikb(
                t('open_logs_chat_button', cb),
                url = url(cb.message.chat.id),
            )],
            [Ikb(
                t('main_menu_button', cb),
                'main_menu_button',
            )],
        ])
    )


async def remove_logs_chat_button(
    client: Client,
    cb: CallbackQuery,
) -> None:
    await l.notify(f'{mention(cb.from_user)} removed logs chat')
    await l.remove()
    await logs_chat_button(
        client,
        cb,
    )


async def logs_chat_button(
    client: Client,
    cb: CallbackQuery,
) -> None:
    if l.logs_chat:
        await cb.message.edit(
            text = t('show_logs_chat_msg', cb),
            reply_markup = Ikm([
                [Ikb(
                    t('open_logs_chat_button', cb),
                    url = url(l.logs_chat.id),
                )],
                [Ikb(
                    t('remove_logs_chat_button', cb),
                    'remove_logs_chat_button',
                )],
                [Ikb(
                    t('replace_logs_chat_button', cb), 
                    url = f't.me/{cb.message.from_user.username}?startgroup=logs',
                )],
                [Ikb(t(
                    'back_to_admin_panel_button', cb),
                    'admin_panel_button',
                )],
            ])
        )
    else:
        await cb.message.edit(
            text = t('set_logs_chat_msg', cb),
            reply_markup = Ikm([
                [Ikb(
                    t('set_logs_chat_button', cb),
                    url = f't.me/{cb.message.from_user.username}?startgroup=logs',
                )],
                [Ikb(
                    t('back_to_admin_panel_button', cb),
                    'admin_panel_button',
                )]
            ])
        )


async def notify_removed(
    msg: Message,
) -> None:
    if msg.left_chat_member.id != config.me.id:
        return
    if msg.chat.id != config.logs_chat_id:
        return
    await l.remove()
    await l.notify(
        f'{mention(msg.from_user)} removed me from logs chat'
    )

