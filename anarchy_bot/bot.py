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
    is_wrong_msg,
    get_end_int,
    mention,
    chats,
)


class Perms():
    def __init__(
        self,
        initiator: User,
        user_to_mute: User,
    ):
        self.initiator = initiator
        self.user_to_mute = user_to_mute
        self.perms_unmuted = ChatPermissions(
            can_send_messages=True,
            can_send_media_messages=True,
            can_send_other_messages=True,
            can_send_polls=True,
            can_add_web_page_previews=True,
            can_change_info=True,
            can_invite_users=True,
           can_pin_messages=True,
        )
        self.perms_muted = ChatPermissions(
            can_send_messages=False,
            can_send_media_messages=False,
            can_send_other_messages=False,
            can_send_polls=False,
            can_add_web_page_previews=False,
            can_change_info=False,
            can_invite_users=False,
            can_pin_messages=False,
        )

    async def unmute_and_edit(
        self,
        text: str,
        client: Client,
        msg_to_edit: Message,
    ):
        change_permissions_method = client.restrict_chat_member(
            chat_id=msg_to_edit.chat.id,
            user_id=self.user_to_mute.id,
            permissions=self.perms_unmuted,
        )
        error = await self.change_permissions(
            change_permissions_method=change_permissions_method,
        )
        if error:
            await msg_to_edit.edit(error)
        else:
            await msg_to_edit.edit(text)

    async def mute_and_edit(
        self,
        text: str,
        client: Client,
        msg_to_edit: Message,
        until_date: datetime.datetime,
    ):
        change_permissions_method = client.restrict_chat_member(
            chat_id=msg_to_edit.chat.id,
            user_id=self.user_to_mute.id,
            permissions=self.perms_muted,
            until_date=until_date,
        )
        error = await self.change_permissions(
            change_permissions_method=change_permissions_method,
        )
        if error:
            await msg_to_edit.edit(error)
        else:
            await msg_to_edit.edit(text)

    async def mute_or_del(
        self,
        text: str,
        client: Client,
        msg_to_del: Message,
        until_date: datetime.datetime,
    ):
        if not self.user_to_mute:
            await self.delete(msg_to_del)
            return
        change_permissions_method = client.restrict_chat_member(
            chat_id=msg_to_del.chat.id,
            user_id=self.user_to_mute.id,
            permissions=self.perms_muted,
            until_date=until_date,
        )
        error = await self.change_permissions(
            change_permissions_method=change_permissions_method,
        )
        if error:
            await self.delete(msg_to_del)
        else:
            await msg_to_del.reply(text)

    async def delete(
        self,
        msg_to_del: Message,
    ):
        try:
            await msg_to_del.delete()
        except pyrogram.errors.MessageDeleteForbidden:
            await msg_to_del.reply(t('permissions_msg', self.initiator))

    async def change_permissions(
        self,
        change_permissions_method,
    ) -> str:
        '''
        returns empty str on success, str with error on error
        '''
        try:
            await change_permissions_method
        except pyrogram.errors.ChatAdminRequired:
                return t('permissions_msg', self.initiator)
        except (
            pyrogram.errors.UserAdminInvalid,
            pyrogram.errors.RightForbidden,
        ):
            if self.initiator.id == self.user_to_mute.id:
                return f'you are bigger admin than me'
            else:
                return f'{mention(self.user_to_mute)} is bigger admin than me'
        else:
            return ''


class Votes:
    def __init__(
        self,
        user_to_mute: User,
        initiator: User,
        client: Client,
    ) -> None:
        self.user_to_mute: User = user_to_mute
        self.plus_dict: dict[int, User] = {}
        self.minus_dict: dict[int, User] = {}
        self.initiator: User = initiator
        self.msg_to_edit: Message | None = None
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
        if not self.msg_to_edit:
            raise ValueError
        updated = await self.get_updated_message()
        try:
            await self.msg_to_edit.edit(**updated)
        except:
            pass

    async def reply(
        self,
        msg_to_reply: Message
    ):
        updated_message = await self.get_updated_message()
        self.msg_to_edit = await msg_to_reply.reply(**updated_message)

    async def done(
        self,
    ):
        if not self.msg_to_edit:
            raise ValueError
        perms = Perms(
            initiator=self.initiator,
            user_to_mute=self.user_to_mute,
        )
        count = len(self.plus_dict) - len(self.minus_dict)
        if count >= 2:
            minutes = count * 30
            await perms.mute_and_edit(
                text=f'{mention(self.user_to_mute)} was muted for {minutes} minutes' + self.get_voters(),
                client=self.client,
                msg_to_edit=self.msg_to_edit,
                until_date=datetime.datetime.now() + datetime.timedelta(
                    minutes = minutes,
                ),
            )
        else:
            await perms.unmute_and_edit(
                text=f'{mention(self.user_to_mute)} was unmuted, mute votes must exceed unmute by 2 for successfull mute' + self.get_voters(),
                client=self.client,
                msg_to_edit=self.msg_to_edit,
            )

        chat_id = self.msg_to_edit.chat.id
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
            self.initiator,
        ).format(
            user=mention(self.user_to_mute)
        ) + self.get_voters()
        buttons = [
            [Ikb(
                t('mute_plus_button', self.initiator),
                f'mute_plus_button_{self.user_to_mute.id}',
            )],
            [Ikb(
                t('mute_minus_button', self.initiator),
                f'mute_minus_button_{self.user_to_mute.id}',
            )],
            [Ikb(
                t('mute_done_button', self.initiator),
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
    if await is_wrong_msg(msg):
        return
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
    if await is_wrong_msg(msg):
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
            initiator=msg.from_user,
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


async def selfmute(
    client: Client,
    msg: Message,
) -> None:
    if await is_wrong_msg(msg):
        return
    msg_to_edit = await msg.reply(
        'trying to mute you'
    )
    perms = Perms(
        initiator=msg.from_user,
        user_to_mute=msg.from_user,
        success_msg=f'succesfully muted you for 1 hour',
    )
    await perms.mute_and_edit(
        client=client,
        msg_to_edit=msg_to_edit,
        until_date=datetime.datetime.now() + datetime.timedelta(
            hours=1,
        ),
    )
    

async def selfmute_del(
    client: Client,
    msg: Message,
) -> None:
    if msg.chat.type != pyrogram.enums.ChatType.SUPERGROUP:
        await msg.reply(
            'wrong chat type, expected supergroup, got ' + str(msg.chat.type).lower()
        )
        return
    perms = Perms(
        initiator=msg.from_user,
        user_to_mute=msg.from_user,
        success_msg=f'succesfully minuted you for 1 hour',
    )
    await perms.mute_or_del(
        client=client,
        msg_to_del=msg,
        until_date=datetime.datetime.now() + datetime.timedelta(
            hours=1,
        ),
    )

