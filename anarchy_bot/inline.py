# license is gnu agpl 3 - gnu.org/licenses/agpl-3.0.en.html

import pyrogram as pg
from lang import t
from pyrogram.client import Client
from pyrogram.types import (
    InlineKeyboardButton as Ikb,
    InlineKeyboardMarkup as Ikm,
    InlineQueryResultArticle,
    InputTextMessageContent,
    CallbackQuery,
    InlineQuery,
    ChatPreview,
    Message,
    Chat,
    User,
)
from config import (
    config,
)
from common import (
    write_error,
    get_buttons,
    c,
    l,
)


async def catched_on_inline(
    client: Client,
    inline: InlineQuery,
):
    try:
        await on_inline(
            client,
            inline,
        )
    except Exception:
        await l.log(
            file = write_error()
        )


async def on_inline(
    client: Client,
    inline: InlineQuery,
) -> None:
    c.log(inline)
    if inline.from_user.id not in config.admins:
        await inline.answer(
            results = [],
            is_personal = True,
            cache_time = 0,
        )
    await inline.answer(
        results = [InlineQueryResultArticle(
            title = t('promote_to_admin_button', inline),
            input_message_content = InputTextMessageContent(
                t('request_admin_rights_message', inline),
            ),
            reply_markup = get_buttons([['request_admin_rights_button']], inline),
        )],
        is_personal = True,
        cache_time = 0,
    )

