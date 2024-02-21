# license is gnu agpl 3 - gnu.org/licenses/agpl-3.0.en.html

import pyrogram as pg
from lang import t
from pyrogram.client import Client
from pyrogram.types import (
    InlineKeyboardButton as Ikb,
    InlineKeyboardMarkup as Ikm,
    CallbackQuery,
    ChatPreview,
    Message,
    Chat,
    User,
)
from config import (
    config,
    c,
)
from common import (
    get_two_end_int,
    get_end_int,
    write_error,
    mention,
    url,
    chats,
)


async def pages_button(
    client: Client,
    cb: CallbackQuery,
    page_size: int = 5,
) -> None:
    chat_type = str(cb.data).replace(
        '_pages_button',
        '',
    ).replace(
        'list_bot_',
        '',
    )
    all_items = list(chats.users_dict.keys()) # TODO
    pages_count = (len(all_items) + page_size - 1) // page_size
    index = 0
    buttons = []
    while index + 1 <= pages_count:
        buttons.append([])
        for _ in range(0, 10):
            if index + 1 <= pages_count:
                buttons[-1].append(Ikb(
                    text = str(index + 1),
                    callback_data = f'list_bot_{chat_type}_button_{index}',
                ))
                index += 1
    await cb.edit_message_text(
        text = t('choose_page_msg', cb),
        reply_markup = Ikm(buttons),
    )


async def list_bot_users_button(
    client: Client,
    cb: CallbackQuery,
) -> None:
    opened_page = await get_end_int(cb)
    if opened_page is None:
        return
    users_dict: dict[int, str] = {}
    users_ids = list(chats.users_dict.keys())
    users_ids_chunk = await get_chunk(
        items_ids_list = users_ids,
        opened_page = opened_page,
        cb = cb,
    )
    if not users_ids:
        await cb.answer(
            t('no_bot_users_cb', cb),
            show_alert = True,
        )
        return
    if not users_ids_chunk:
        return
    for user_id in users_ids_chunk:
        try:
            user = await client.get_users(
                user_id
            )
        except Exception:
            users_dict[user_id] = str(user_id)
            continue
        if isinstance(
            user,
            list,
        ):
            user = user[0]
        if user.username:
            users_dict[user.id] = f'@{user.username}'
        else:
            users_dict[user.id] = user.first_name
    await get_list(
        page = opened_page,
        items_dict = users_dict,
        chat_type = 'users',
        all_items = users_ids,
        cb = cb,
    )


async def list_bot_admins_button(
    client: Client,
    cb: CallbackQuery,
) -> None:
    opened_page = await get_end_int(cb)
    if opened_page is None:
        return
    if not config.admins:
        await cb.answer(
            t('no_bot_admins_cb', cb),
            show_alert = True,
        )
        return
    admins_dict: dict[int, str] = {}
    admins_ids_chunk = await get_chunk(
        items_ids_list = config.admins,
        opened_page = opened_page,
        cb = cb,
    )
    if not admins_ids_chunk:
        return
    for admin_id in admins_ids_chunk:
        try:
            admin = await client.get_users(
                admin_id
            )
        except Exception:
            admins_dict[admin_id] = str(admin_id)
            continue
        if isinstance(
            admin,
            list,
        ):
            admin = admin[0]
        if admin.username:
            admins_dict[admin.id] = f'@{admin.username}'
        else:
            admins_dict[admin.id] = admin.first_name
    await get_list(
        page = opened_page,
        items_dict = admins_dict,
        chat_type = 'admins',
        all_items = config.admins,
        cb = cb,
        extra_button = Ikb(
            t('add_admin_button', cb),
            switch_inline_query = '',
        )
    )


async def list_bot_chats_button(
    client: Client,
    cb: CallbackQuery,
) -> None:
    opened_page = await get_end_int(cb)
    if opened_page is None:
        return
    if not chats.chats_dict:
        await cb.answer(
            t('no_bot_chats_cb', cb),
            show_alert = True,
        )
        return
    chats_dict: dict[int, str] = {}
    chats_ids_list = list(chats.chats_dict.keys())
    chats_ids_chunk = await get_chunk(
        items_ids_list = chats_ids_list,
        opened_page = opened_page,
        cb = cb,
    )
    if not chats_ids_chunk:
        return
    for chat_id in chats_ids_chunk:
        try:
            chat = await client.get_chat(chat_id)
        except:
            chat = None
        if chat:
            if isinstance(
                chat,
                Chat,
            ):
                if chat.username:
                    chats_dict[chat_id] = f'@{chat.username}'
                else:
                    chats_dict[chat_id] = chat.title
            else:
                chats_dict[chat_id] = chat.title
        else:
            chats_dict[chat_id] = str(chat_id)
    await get_list(
        page = opened_page,
        items_dict = chats_dict,
        chat_type = 'chats',
        all_items = chats_ids_list,
        cb = cb,
        extra_button = Ikb(
            t('add_to_new_chat_button', cb),
            url = f't.me/{cb.message.from_user.username}?startgroup',
        )
    )


async def get_list(
    page: int,
    items_dict: dict[int, str],
    chat_type: str,
    all_items: list,
    cb,
    extra_button: Ikb | None = None,
) -> None:
    pages_count = (
        len(all_items) + config.page_size - 1
    ) // config.page_size
    buttons = []
    for item_id, item_name in items_dict.items():
        buttons.append([Ikb(
            str(item_name),
            f'get_bot_{chat_type}_button_{item_id}_{page}',
        )])
    controls = []
    if page == 0:
        controls.append(
            Ikb('❌', 'first_page_button')
        )
    else:
        controls.append(Ikb(
            '◄',
            f'list_bot_{chat_type}_button_{page - 1}',
        ))
    controls.append(Ikb(
        f'{page + 1}/{pages_count}',
        f'list_bot_{chat_type}_pages_button',
    ))
    if page + 1 >= pages_count:
        controls.append(
            Ikb('❌', 'last_page_button')
        )
    else:
        controls.append(Ikb(
            '►',
            f'list_bot_{chat_type}_button_{page + 1}',
        ))
    buttons.append(controls)
    if extra_button:
        buttons.append([extra_button])
    buttons.append([Ikb(
        t('back_to_admin_panel_button', cb),
        'admin_panel_button',
    )])
    await cb.message.edit(
        text = t(f'there_are_bot_{chat_type}_msg', cb),
        reply_markup = Ikm(buttons),
    )


async def get_bot_users_button(
    client: Client,
    cb: CallbackQuery,
    chat_type: str,
) -> None:
    end = await get_two_end_int(cb)
    if end is None:
        return
    user_id, page = end
    try:
        user = await client.get_users(
            user_id
        )
    except Exception:
        await cb.message.reply_document(
            document = write_error(),
            caption = 'got error while getting user',
            quote = True,
        )
        return
    if isinstance(
        user,
        list,
    ):
        return await cb.answer('error: got list instead of user')
    buttons = Ikm([
        [Ikb(
            t('more_info_button', cb),
            f'more_info_{chat_type}_button_{user.id}_{page}',
        )],
        [Ikb(
            t('back_to_admin_panel_button', cb),
            'admin_panel_button',
        )],
        [Ikb(
            t(f'back_to_bot_{chat_type}_list_button', cb),
            f'list_bot_{chat_type}_button_{page}',
        )],
    ])
    text = mention(user)
    await cb.edit_message_text(
        text = text,
        reply_markup = buttons,
    )


async def get_bot_chats_button(
    client: Client,
    cb: CallbackQuery,
) -> None:
    end = await get_two_end_int(cb)
    if end is None:
        return
    chat_id, page = end
    buttons = Ikm([
        [Ikb(
            t('more_info_button', cb),
            f'more_info_chats_button_{chat_id}_{page}',
        )],
        [Ikb(
            t('back_to_admin_panel_button', cb),
            'admin_panel_button',
        )],
        [Ikb(
            t(f'back_to_bot_chats_list_button', cb),
            f'list_bot_chats_button_{page}',
        )],
    ])
    await cb.edit_message_text(
        text = url(chat_id),
        reply_markup = buttons,
    )


async def more_info_users_button(
    client: Client,
    cb: CallbackQuery,
    chat_type: str,
) -> None:
    end = await get_two_end_int(cb)
    if end is None:
        return
    user_id, page = end
    try:
        user = await client.get_users(
            user_id
        )
    except Exception:
        await cb.message.reply_document(
            document = write_error(),
            caption = 'got error while getting user',
            quote = True,
        )
        return
    if isinstance(
        user,
        list,
    ):
        return await cb.answer('error: got list instead of user')
    buttons = Ikm([
        [Ikb(
            t('back_to_admin_panel_button', cb),
            'admin_panel_button',
        )],
        [Ikb(
            t(f'back_to_bot_{chat_type}_list_button', cb),
            f'list_bot_{chat_type}_button_{page}',
        )],
        [Ikb(
            t('shrink_button', cb),
            f'get_bot_{chat_type}_button_{user.id}_{page}',
        )],
    ])
    text = f'''
username: @{user.username}
mention: {user.mention()}
id: {user.id}
phone_number: {user.phone_number}
first_name: {user.first_name}
last_name: {user.last_name}
is_deleted: {user.is_deleted}
is_premium: {user.is_premium}
online_status: {user.status}
last_online_date: {user.last_online_date}
language_code: {user.language_code}
dc_id: {user.dc_id}
restrictions: {user.restrictions}
'''
    await cb.edit_message_text(
        text = text,
        reply_markup = buttons,
    )


async def more_info_chats_button(
    client: Client,
    cb: CallbackQuery,
) -> None:
    end = await get_two_end_int(cb)
    if end is None:
        return
    chat_id, page = end
    try:
        chat = await client.get_chat(
            chat_id
        )
    except Exception:
        await cb.message.reply_document(
            document = write_error(),
            caption = 'got error while getting chat',
            quote = True,
        )
        return
    if isinstance(
        chat,
        ChatPreview,
    ):
        text = f'''
got chat preview

link: {url(chat_id)}
title: {chat.title}
id: {chat_id}
members_count: {chat.members_count}
'''
    else:
        text = f'''
username: @{chat.username}
id: {chat.id}
title: {chat.title}
first_name: {chat.first_name}
last_name: {chat.last_name}
dc_id: {chat.dc_id}
restrictions: {chat.restrictions}
members_count: {chat.members_count}
bio: {chat.bio}
description: {chat.description}
'''
    buttons = Ikm([
        [Ikb(
            t('back_to_admin_panel_button', cb),
            'admin_panel_button',
        )],
        [Ikb(
            t(f'back_to_bot_chats_list_button', cb),
            f'list_bot_chats_button_{page}',
        )],
    ])
    await cb.edit_message_text(
        text = text,
        reply_markup = buttons,
    )


async def get_chunk(
    items_ids_list: list[int],
    opened_page: int,
    cb: CallbackQuery,
) -> None | list[int]:
    first_item = config.page_size * opened_page
    chunk = items_ids_list[first_item : first_item + config.page_size]
    if chunk:
        return chunk
    else:
        await cb.answer(
            t('wrong_page_cb', cb),
        )
        return

