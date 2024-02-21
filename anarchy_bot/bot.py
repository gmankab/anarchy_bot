# license is gnu agpl 3 - gnu.org/licenses/agpl-3.0.en.html

import pyrogram.enums
import pyrogram.errors
import asyncio
import random
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
    tag = splitted[-1][:16]
    if msg.chat.type != pyrogram.enums.ChatType.SUPERGROUP:
        responce: Message = await msg.reply(
            'wrong chat type, expected supergroup, got ' + str(msg.chat.type).lower()
        )
        return
    if not msg.from_user:
        responce: Message = await msg.reply(
            'you must send message as user, not as channel or chat'
        )
        return
    responce: Message = await msg.reply(
        text = f'trying to make {mention(msg.from_user)} an admin...'
    )
    text = await promote_to_admin(
        responce = responce,
        client = client,
        msg = msg,
    )
    counter = 0
    while True:
        counter += 1
        await asyncio.sleep(1)
        try:
            await client.set_administrator_title(
                chat_id = msg.chat.id,
                user_id = msg.from_user.id,
                title = tag,
            )
        except ValueError:
            if counter > 5:
                await responce.edit_text(
                    f'error: telegram says you are still not admin'
                )
                return
            else:
                continue
        else:
            text += f' with title {tag}'
            await responce.edit_text(
                text
            )
            return


async def promote_to_admin(
    responce: Message,
    client: Client,
    msg: Message,
) -> str:
    counter = 0
    demoted_message: str = ''
    while True:
        counter += 1
        if counter > 4:
            await responce.edit_text('error: 4 bad attempts')
            return ''
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
        except pyrogram.errors.ChatAdminRequired:
            await responce.edit_text(
                'i am not admin in this chat'
            )
            return ''
        except pyrogram.errors.RightForbidden:
            await responce.edit_text(
                'you are bigger admin than me'
            )
            return ''
        except pyrogram.errors.UserCreator:
            await responce.edit_text(
                'you are chat owner'
            )
            return ''
        except pyrogram.errors.AdminsTooMuch:
            demoted_message = await demote(
                client = client,
                msg = msg,
                responce = responce,
            )
            if demoted_message:
                continue
            else:
                return ''
        else:
            promoted_message = f'{mention(msg.from_user)} promoted to admin'
            if demoted_message:
                promoted_message = demoted_message + '\n\n' + promoted_message
            await responce.edit_text(
                promoted_message
            )
            return promoted_message


async def demote(
    client: Client,
    msg: Message,
    responce: Message
) -> str:
    admins: list[ChatMember] = await chats.list_chat_admins(
        client = client,
        chat = msg.chat,
    )
    while admins:
        admin: ChatMember = random.choice(admins)
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
            message = f'too many admins, demoting {mention(admin.user)}'
            await responce.edit_text(
                message
            )
            return message
        except pyrogram.errors.UserCreator:
            admins.remove(admin)
            continue
        except Exception:
            admins.remove(admin)
            print(
                f'failed to demote {admin.user.first_name}'
            )
            continue
    await responce.edit_text(
        f'too many admins, no admin available to demote'
    )
    return ''

