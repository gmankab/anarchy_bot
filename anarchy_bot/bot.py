# license is gnu agpl 3 - gnu.org/licenses/agpl-3.0.en.html

import pyrogram.enums
import pyrogram.errors
import asyncio
import random
import datetime
from lang import t
from pyrogram.client import Client
from pyrogram.types import (
    InlineKeyboardButton as Ikb,
    InlineKeyboardMarkup as Ikm,
    ChatPermissions,
    ChatPrivileges,
    CallbackQuery,
    ChatMember,
    Message,
    User,
)
from common import (
    IgnoreError,
    mention_nolink,
    get_end_int,
    mention,
    chats,
)


class Votes:
    def __init__(
        self,
        user_to_mute: User,
        user_who_votes: User,
        client: Client,
    ) -> None:
        self.user_to_mute: User = user_to_mute
        self.plus_dict: dict[int, User] = {}
        self.minus_dict: dict[int, User] = {}
        self.language: User = user_who_votes
        self.msg: Message | None = None
        self.client: Client = client

    async def vote_minus(
        self,
        user_who_votes: User,
        cb: CallbackQuery | None,
    ):
        while user_who_votes.id in self.plus_dict:
            self.plus_dict.pop(user_who_votes.id)
        if user_who_votes.id in self.minus_dict:
            if cb:
                await cb.answer('already voted for +30 minutes')
        else:
            self.minus_dict[user_who_votes.id] = user_who_votes
            if cb:
                await cb.answer('voted for +30 minutes')

    async def vote_plus(
        self,
        user_who_votes: User,
        cb: CallbackQuery | None,
    ):
        while user_who_votes.id in self.minus_dict:
            self.minus_dict.pop(user_who_votes.id)
        if user_who_votes.id in self.plus_dict:
            if cb:
                await cb.answer('already voted for +30 minutes')
        else:
            self.plus_dict[user_who_votes.id] = user_who_votes
            if cb:
                await cb.answer('voted for -30 minutes')

    async def update(
        self,
    ):
        if not self.msg:
            raise ValueError
        updated = await self.get_updated_message()
        try:
            await self.msg.edit(**updated)
        except:
            pass

    async def reply(
        self,
        msg_to_reply: Message
    ):
        updated_message = await self.get_updated_message()
        self.msg = await msg_to_reply.reply(**updated_message)

    async def done(
        self,
    ):
        if not self.msg:
            raise ValueError
        count = len(self.plus_dict) - len(self.minus_dict)
        if count >= 2:
            await self.mute(count)
        else:
            await self.unmute()


    async def restrict_chat_member(
        self,
        text: str,
        permissions: ChatPermissions,
        until_date: datetime.datetime | None = None,
    ):
        if until_date:
            kwargs = {
                'until_date': until_date,
            }
        else:
            kwargs = {}
        if not self.msg:
            raise TypeError()
        try:
            await self.client.restrict_chat_member(
                chat_id=self.msg.chat.id,
                user_id=self.user_to_mute.id,
                permissions=permissions,
                **kwargs,
            )
        except pyrogram.errors.ChatAdminRequired:
            await self.msg.edit(
                text=t('permissions_msg', self.language),
            )
        except pyrogram.errors.UserAdminInvalid:
            await self.msg.edit(
                text=f'{mention(self.user_to_mute)} is bigger admin than me',
            )
        except pyrogram.errors.RightForbidden:
            await self.msg.edit(
                text=f'{mention(self.user_to_mute)} is bigger admin than me',
            )
        except pyrogram.errors.UserCreator:
            await self.msg.edit(
                text=f'{mention(self.user_to_mute)} is chat owner',
            )
        else:
            await self.msg.edit(
                text=text,
            )
        self.msg.reply_markup
        chat_id = self.msg.chat.id
        messages_dict = chats.mute_votes.get(chat_id)
        if messages_dict is None:
            keys = list(chats.mute_votes.keys())
            raise KeyError(
                f'can not get {chat_id} from {keys}'
            )
        messages_dict.pop(
            self.user_to_mute.id,
            None,
        )

    async def unmute(
        self,
    ):
        if not self.msg:
            raise ValueError
        permissions = ChatPermissions(
            can_send_messages=True,
            can_send_media_messages=True,
            can_send_other_messages=True,
            can_send_polls=True,
            can_add_web_page_previews=True,
            can_change_info=True,
            can_invite_users=True,
            can_pin_messages=True,
        )
        await self.restrict_chat_member(
            permissions=permissions,
            text=f'{mention(self.user_to_mute)} was unmuted, mute votes must exceed unmute by 2 for successfull mute' + self.get_voters(),
        )

    async def mute(
        self,
        count: int,
    ):
        if not self.msg:
            raise ValueError
        permissions = ChatPermissions(
            can_send_messages=False,
            can_send_media_messages=False,
            can_send_other_messages=False,
            can_send_polls=False,
            can_add_web_page_previews=False,
            can_change_info=False,
            can_invite_users=False,
            can_pin_messages=False,
        )
        minutes = count * 30
        await self.restrict_chat_member(
            permissions=permissions,
            text=f'{mention(self.user_to_mute)} was muted for {minutes} minutes' + self.get_voters(),
            until_date=datetime.datetime.now() + datetime.timedelta(
                minutes = minutes,
            ),
        )

    def get_voters(
        self,
    ) -> str:
        text = ''
        if self.plus_dict:
            text += '\n\nvotes for mute:'
            for user in self.plus_dict.values():
                text += '\n' + mention(user)
        if self.minus_dict:
            text += '\n\nvotes against mute:'
            for user in self.minus_dict.values():
                text += '\n' + mention(user)
        return text

    async def get_updated_message(
        self,
    ) -> dict:
        text = t(
            'mute_msg',
            self.language,
        ).format(
            user=mention(self.user_to_mute)
        ) + self.get_voters()
        buttons = [
            [Ikb(
                t('mute_plus_button', self.language),
                f'mute_plus_button_{self.user_to_mute.id}',
            )],
            [Ikb(
                t('mute_minus_button', self.language),
                f'mute_minus_button_{self.user_to_mute.id}',
            )],
            [Ikb(
                t('mute_done_button', self.language),
                f'mute_done_button_{self.user_to_mute.id}',
            )],
        ]
        return {
            'text': text,
            'reply_markup': Ikm(buttons),
        }


async def becomeadmin(
    client: Client,
    msg: Message,
) -> None:
    splitted = msg.text.split(' ', 1)
    if len(splitted) == 1:
        admins: list[ChatMember] = await chats.list_chat_admins(
            client=client,
            chat=msg.chat,
        )
        tag = ''
        while admins:
            admin: ChatMember = random.choice(admins)
            tag: str = admin.custom_title
            if tag:
                break
            else:
                admins.remove(admin)
                continue
        if not tag:
            tag = 'admin'
    else:
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
        responce=responce,
        client=client,
        msg=msg,
        user=msg.from_user,
    )
    counter = 0
    while True:
        counter += 1
        await asyncio.sleep(1)
        try:
            await client.set_administrator_title(
                chat_id=msg.chat.id,
                user_id=msg.from_user.id,
                title=tag,
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
    user: User,
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
                chat_id=msg.chat.id,
                user_id=msg.from_user.id,
                privileges=ChatPrivileges(
                    can_manage_chat=True,
                    can_change_info=True,
                    can_invite_users=True,
                ),
            )
        except pyrogram.errors.ChatAdminRequired:
            await responce.edit_text(
                t('permissions_msg', user)
            )
            return ''
        except pyrogram.errors.UserAdminInvalid:
            await responce.edit_text(
                'you are bigger admin than me'
            )
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
                client=client,
                msg_to_edit=responce,
                begin_log='too many admins, '
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
    msg_to_edit: Message,
    begin_log: str = '',
) -> str:
    admins: list[ChatMember] = await chats.list_chat_admins(
        client=client,
        chat=msg_to_edit.chat,
    )
    while admins:
        admin: ChatMember = random.choice(admins)
        try:
            await client.promote_chat_member(
                chat_id=msg_to_edit.chat.id,
                user_id=admin.user.id,
                privileges=ChatPrivileges(
                    can_manage_video_chats=False,
                    can_restrict_members=False,
                    can_promote_members=False,
                    can_delete_messages=False,
                    can_post_messages=False,
                    can_edit_messages=False,
                    can_invite_users=False,
                    can_pin_messages=False,
                    can_change_info=False,
                    can_manage_chat=False,
                    is_anonymous=False,
                ),
            )
            message = f'{begin_log}demoting {mention(admin.user)}'
            await msg_to_edit.edit_text(
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
    await msg_to_edit.edit_text(
        f'{begin_log}no admin available to demote'
    )
    return ''


async def mute(
    client: Client,
    msg: Message,
) -> None:
    if msg.chat.type != pyrogram.enums.ChatType.SUPERGROUP:
        await msg.reply(
            'wrong chat type, expected supergroup, got ' + str(msg.chat.type).lower()
        )
        return
    if not msg.from_user:
        await msg.reply(
            'you must send message as user, not as channel or chat'
        )
        return
    if not msg.reply_to_message:
        await msg.reply(
            'you should reply to someone\'s message'
        )
        return
    user_to_mute = msg.reply_to_message.from_user
    if not user_to_mute:
        await msg.reply(
            'i can\'t mute channel or chat'
        )
        return
    chat_id = msg.chat.id
    if chat_id not in chats.mute_votes:
        chats.mute_votes[chat_id] = {}
    if user_to_mute.id not in chats.mute_votes[chat_id]:
        chats.mute_votes[chat_id][user_to_mute.id] = Votes(
            user_to_mute=user_to_mute,
            user_who_votes=msg.from_user,
            client=client,
        )
    votes = get_votes_from_int(
        chat_id=msg.chat.id,
        user_to_mute_id=user_to_mute.id,
    )
    await votes.vote_plus(
        user_who_votes=msg.from_user,
        cb=None,
    )
    await votes.reply(msg)


def get_votes_from_int(
    chat_id: int,
    user_to_mute_id: int,
) -> Votes:
    messages_dict = chats.mute_votes.get(chat_id)
    if messages_dict is None:
        keys = list(chats.mute_votes.keys())
        raise KeyError(
            f'can not get {chat_id} from {keys}'
        )
    votes: Votes = messages_dict.get(user_to_mute_id)
    if votes is None:
        keys = list(messages_dict.keys()),
        raise KeyError(
            f'can not get {user_to_mute_id} from {keys}'
        )
    return votes


async def get_votes_from_cb(
    cb: CallbackQuery,
) -> Votes:
    user_to_mute_id: int | None = await get_end_int(cb)
    if not user_to_mute_id:
        raise IgnoreError
    chat_id = cb.message.chat.id
    messages_dict = chats.mute_votes.get(chat_id)
    if messages_dict is None:
        keys = list(chats.mute_votes.keys())
        await cb.answer(
            f'can not get {chat_id} from {keys}'
        )
        raise IgnoreError
    votes: Votes = messages_dict.get(user_to_mute_id)
    if votes is None:
        keys = list(messages_dict.keys()),
        await cb.answer(
            f'can not get {user_to_mute_id} from {keys}'
        )
        raise IgnoreError
    return votes


async def mute_plus_button(
    _: Client,
    cb: CallbackQuery,
) -> None:
    if not cb.from_user:
        await cb.answer(
            'channels and chats can\'t vote'
        )
    votes = await get_votes_from_cb(cb)
    await votes.vote_plus(
        user_who_votes=cb.from_user,
        cb = cb,
    )
    await votes.update()


async def mute_minus_button(
    _: Client,
    cb: CallbackQuery,
) -> None:
    if not cb.from_user:
        await cb.answer(
            'channels and chats can\'t vote'
        )
        return
    votes = await get_votes_from_cb(cb)
    await votes.vote_minus(
        user_who_votes=cb.from_user,
        cb = cb,
    )
    await votes.update()


async def mute_done_button(
    _: Client,
    cb: CallbackQuery,
) -> None:
    if not cb.from_user:
        await cb.answer(
            'channels and chats can\'t press this button'
        )
        return
    permitted = cb.message.reply_to_message.from_user
    if cb.from_user.id != permitted.id:
        await cb.answer(f'this button for {mention_nolink(permitted)}')
        return
    votes = await get_votes_from_cb(cb)
    await votes.done()

