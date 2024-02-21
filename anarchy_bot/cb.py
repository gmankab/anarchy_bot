# license is gnu agpl 3 - gnu.org/licenses/agpl-3.0.en.html

from lang import t
from pyrogram.client import Client
from pyrogram.types import (
    InlineKeyboardButton as Ikb,
    InlineKeyboardMarkup as Ikm,
    CallbackQuery,
)
from bot import (
    mute_done_button,
    mute_minus_button,
    mute_plus_button,
)
from config import (
    config,
    c,
)
from common import (
    filter_admin,
    get_end_int,
    get_buttons,
    write_error,
    bad_button,
    mention,
    chats,
    l,
)
from lists import (
    get_bot_users_button,
    more_info_chats_button,
    more_info_users_button,
    list_bot_admins_button,
    list_bot_users_button,
    list_bot_chats_button,
)
from chats import (
    confirm_set_logs_chat_button,
    remove_logs_chat_button,
    logs_chat_button,
)


async def catched_on_cb(
    client: Client,
    cb: CallbackQuery,
):
    try:
        await on_cb(
            client,
            cb,
        )
    except Exception:
        await l.log(
            file = write_error()
        )


async def on_cb(
    client: Client,
    cb: CallbackQuery,
) -> None:
    c.log(f'got callback {cb.data} from user {cb.from_user.id}')
    users = {
        'request_admin_rights_button': request_admin_rights_button,
        'back_main_button': back_main_button,
        'main_menu_button': main_menu_button,
    }
    users_in = {
        'promote_to_admin_button_': promote_to_admin_button,
        'mute_minus_button_': mute_minus_button,
        'mute_plus_button_': mute_plus_button,
        'mute_done_button_': mute_done_button,
    }
    answers = {
        'first_page_button': 'first_page_cb',
        'last_page_button': 'last_page_cb',
    }
    admins = {
        'confirm_set_logs_chat_button': confirm_set_logs_chat_button,
        'remove_logs_chat_button': remove_logs_chat_button,
        'admin_panel_button': admin_panel_button,
        'logs_chat_button': logs_chat_button,
    }
    admins_in = {
        'list_bot_users_button_': list_bot_users_button,
        'list_bot_chats_button_': list_bot_chats_button,
        'list_bot_admins_button_': list_bot_admins_button,
        'more_info_chats_button_': more_info_chats_button,
    }
    admins_get_user = {
        'get_bot_admins_button_': 'admins',
        'get_bot_users_button_': 'users',
    }
    admins_more_info_user = {
        'more_info_admins_button_': 'admins',
        'more_info_users_button_': 'users',
    }
    for excpected_cb, func in users.items():
        if excpected_cb == cb.data:
            await func(client, cb)
            return await cb.answer(text = '')
    for excpected_cb, func in users_in.items():
        if excpected_cb in str(cb.data):
            await func(client, cb)
            return await cb.answer(text = '')
    for excpected_cb, answer in answers.items():
        if excpected_cb == cb.data:
            return await cb.answer(
                text = t(answer, cb)
            )
    for excpected_cb, func in admins.items():
        if excpected_cb == cb.data:
            if await filter_admin(cb):
                return
            await func(client, cb)
            return await cb.answer(text = '')
    for excpected_cb, func in admins_in.items():
        if excpected_cb in str(cb.data):
            if await filter_admin(cb):
                return
            await func(client, cb)
            return await cb.answer(text = '')
    for excpected_cb, chat_type in admins_get_user.items():
        if excpected_cb in str(cb.data):
            if await filter_admin(cb):
                return
            await get_bot_users_button(client, cb, chat_type)
            return await cb.answer(text = '')
    for excpected_cb, chat_type in admins_more_info_user.items():
        if excpected_cb in str(cb.data):
            if await filter_admin(cb):
                return
            await more_info_users_button(client, cb, chat_type)
            return await cb.answer(text = '')
    return await bad_button(cb)


async def back_main_button(
    _: Client,
    cb: CallbackQuery,
) -> None:
    await cb.edit_message_text(
       t('help_msg', cb),
    )


async def admin_panel_button(
    _: Client,
    cb: CallbackQuery,
) -> None:
    buttons = [
        [
            'list_bot_admins_button_0',
            'list_bot_users_button_0',
            'list_bot_chats_button_0',
        ],
        [
            'logs_chat_button',
        ],
        ['back_main_button'],
    ]
    await cb.edit_message_text(
        text = t('admin_panel_msg', cb),
        reply_markup = get_buttons(
            buttons,
            cb,
        ),
    )


async def request_admin_rights_button(
    _: Client,
    cb: CallbackQuery,
) -> None:
    if cb.from_user.id in config.admins:
        await cb.answer(
            text = t('chat_partner_must_request_cb', cb),
            show_alert = True,
        )
        return
    await cb.edit_message_text(
        text = t(
            'promote_to_admin_message',
            cb
        ).format(
            user = mention(cb.from_user)
        ),
        reply_markup = Ikm([[Ikb(
            text = t('promote_to_admin_button', cb),
            callback_data = f'promote_to_admin_button_{cb.from_user.id}',
        )]])
    )


async def promote_to_admin_button(
    client: Client,
    cb: CallbackQuery,
) -> None:
    if cb.from_user.id not in config.admins:
        await cb.answer(
            text = t('chat_partner_must_promote_cb', cb),
            show_alert = True,
        )
        return
    promoted_user_id = await get_end_int(cb)
    if promoted_user_id is None:
        return
    try:
        promoted_user = await client.get_users(
            promoted_user_id
        )
    except Exception:
        text = f'failed get user {promoted_user_id}'
        await cb.answer(text)
        await client.send_document(
            chat_id = cb.from_user.id,
            document = write_error(),
            caption = text,
        )
        return
    if isinstance(
        promoted_user,
        list,
    ):
        await cb.answer('error: got list')
        return
    if promoted_user_id not in config.admins:
        config.admins.append(promoted_user.id)
    config.to_disk()
    text = f'{mention(cb.from_user)} successfully promoted {mention(promoted_user)} to admin'
    await cb.edit_message_text(text)
    await l.notify(text)


async def not_coded_yet_button(
    _: Client,
    cb: CallbackQuery,
) -> None:
    await cb.answer(
        t('not_coded_yet', cb)
    )


async def main_menu_button(
    _: Client,
    cb: CallbackQuery,
) -> None:
    chats.users_dict[cb.from_user.id] = None
    await cb.message.reply(
        t('help_msg', cb),
    )

