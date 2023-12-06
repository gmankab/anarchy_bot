# license is gnu agpl 3 - gnu.org/licenses/agpl-3.0.en.html

import pyrogram.enums
import pyrogram.errors
import asyncio
from pyrogram.client import Client
from pyrogram.types import (
    ChatPrivileges,
    ChatMember,
    Message,
)
from common import (
    mention,
    chats,
)


async def becomeadmin(
    client: Client,
    msg: Message,
):
    splitted = msg.text.split(' ', 1)
    if len(splitted) == 1:
        responce: Message = await msg.reply(
            'you must specify your title after /becomeadmin\n\nexample: /becomeadmin bebra'
        )
        return
    title = splitted[-1][:16]
    if msg.chat.type != pyrogram.enums.ChatType.SUPERGROUP:
        responce: Message = await msg.reply(
            'wrong chat type, expected supergroup, got ' + str(msg.chat.type).lower()
        )
        return
    if not msg.from_user:
        responce: Message = await msg.reply(
            'you must send message as user, not as channel or chat'
        )
    responce: Message = await msg.reply(
        text = f'trying to make {mention(msg.from_user)} an admin...'
    )
    texts = []
    while True:
        try:
            await client.promote_chat_member(
                chat_id = msg.chat.id,
                user_id = msg.from_user.id,
                privileges = ChatPrivileges(
                    can_manage_chat = True,
                    can_change_info = True,
                    can_invite_users = True,
                ),
            )
        except (
            pyrogram.errors.ChatAdminRequired,
            pyrogram.errors.RightForbidden,
        ):
            texts.append(
                'i have no rights to make you an admin'
            )
            await responce.edit_text('\n\n'.join(texts))
            return
        except pyrogram.errors.UserCreator:
            texts.append(
                'bro you are chat owner'
            )
            await responce.edit_text('\n\n'.join(texts))
            return
        except pyrogram.errors.AdminsTooMuch:
            is_demoted = await demote(
                client = client,
                msg = msg,
                texts = texts,
                responce = responce,
            )
            if is_demoted:
                continue
            else:
                return
        else:
            texts.append(
                f'succesfully promoted {mention(msg.from_user)} to admin'
            )
            await responce.edit_text('\n\n'.join(texts))
            break
    await asyncio.sleep(1)
    await client.set_administrator_title(
        chat_id = msg.chat.id,
        user_id = msg.from_user.id,
        title = title,
    )
    texts[-1] = f'succesfully promoted {mention(msg.from_user)} to admin with title {title}'
    await responce.edit_text('\n\n'.join(texts))


async def demote(
    client: Client,
    msg: Message,
    texts: list,
    responce: Message
):
    admins: list[ChatMember] = await chats.list_chat_admins(
        client = client,
        chat = msg.chat,
    )
    for admin in admins:
        try:
            await client.promote_chat_member(
                chat_id = msg.chat.id,
                user_id = admin.user.id,
                privileges = ChatPrivileges(
                    can_manage_video_chats = False,
                    can_restrict_members = False,
                    can_promote_members = False,
                    can_delete_messages = False,
                    can_post_messages = False,
                    can_edit_messages = False,
                    can_invite_users = False,
                    can_pin_messages = False,
                    can_change_info = False,
                    can_manage_chat = False,
                    is_anonymous = False,
                ),
            )
            texts.append(
                f'too many admins, demoting {mention(admin.user)}'
            )
            await responce.edit_text('\n\n'.join(texts))
            return True
        except pyrogram.errors.UserCreator:
            continue
        except Exception as e:
            texts.append(
                f'failed to demote {mention(admin.user)}: {e}'
            )
            await responce.edit_text('\n\n'.join(texts))
            continue
    texts.append(
        f'too many admins, no admin available to demote'
    )
    await responce.edit_text('\n\n'.join(texts))
    return False

