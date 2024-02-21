# license is gnu agpl 3 - gnu.org/licenses/agpl-3.0.en.html

import datetime
import rich.console
import pyrogram.enums
import pyrogram.errors
import gmanka_yml as yml
import pyrogram as pg
from lang import t
from pathlib import Path
from pyrogram import errors
from pyrogram.client import Client
from pyrogram.types import (
    InlineKeyboardButton as Ikb,
    InlineKeyboardMarkup as Ikm,
    CallbackQuery,
    ChatPreview,
    InlineQuery,
    ChatMember,
    Message,
    User,
    Chat,
)
from config import (
    app_version,
    chats_path,
    config,
    get,
    c,
)


class IgnoreError(Exception):
    pass


class Chats:
    def __init__(
        self,
        path: Path,
    ) -> None:
        self.path = path
        data: dict = yml.from_file( # type: ignore
            self.path,
            default = {},
            expected_type = dict,
        )
        self.mute_votes: dict = {}
        users_list: list[int] = get(
            data = data,
            item = 'users',
            default = [],
            expected_type = list,
        )
        self.chats_dict: dict[int, list[int]] = get(
            data = data,
            item = 'chats',
            default = {},
            expected_type = dict,
        )
        self.users_dict = {}
        for user in users_list:
            self.users_dict[user] = None

    async def remember_user(
        self,
        user_id: int,
    ) -> None:
        if user_id in self.users_dict:
            return
        self.users_dict[user_id] = None
        self.to_disk()
        await l.log(f'success: new user {user_id} writed to {self.path}')

    async def remember_chat(
        self,
        client: Client,
        chat: Chat,
    ) -> None:
        if chat.id in self.chats_dict:
            return
        ids: list[int] = []
        member: ChatMember | None = None
        async for member in client.get_chat_members( # type: ignore
            chat_id = chat.id,
            filter = pyrogram.enums.ChatMembersFilter.ADMINISTRATORS,
        ):
            if not member:
                continue
            if member.user.is_bot:
                continue
            ids.append(
                member.user.id
            )
        self.chats_dict[chat.id] = ids
        self.to_disk()
        await l.log(f'success: new chat {chat.id} writed to {self.path}')

    async def list_chat_admins(
        self,
        client: Client,
        chat: Chat,
    ) -> list[ChatMember]:
        chat_members_unsorted: list[ChatMember] = []
        chat_members_sorted: list[ChatMember] = []
        ids = []
        async for member in client.get_chat_members( # type: ignore
            chat_id = chat.id,
            filter = pyrogram.enums.ChatMembersFilter.ADMINISTRATORS,
        ):
            if not member:
                continue
            if member.user.is_bot:
                continue
            chat_members_unsorted.append(
                member
            )
        for member_id in self.chats_dict[chat.id]:
            for member in chat_members_unsorted:
                if member.user.id == member_id:
                    chat_members_sorted.append(member)
                    chat_members_unsorted.remove(member)
                    break
        chat_members_sorted += chat_members_unsorted
        for member in chat_members_sorted:
            ids.append(member.user.id)
        self.chats_dict[chat.id] = ids
        self.to_disk()
        return chat_members_sorted


    def to_disk(
        self,
    ) -> None:
        if not self.path:
            c.log(hl('error: not writed because path not specified'))
            return
        self.path.parent.mkdir(
            parents = True,
            exist_ok = True,
        )
        yml.to_file(
            data = {
                'version': app_version,
                'users': list(self.users_dict.keys()),
                'chats': self.chats_dict,
            },
            path = self.path,
        )


class Logs:
    def __init__(self) -> None:
        self.logs_chat: Chat | None = None

    async def init(
        self,
        client: Client,
        logs_chat: Chat | None = None,
    ) -> None:
        self.client: Client = client
        if logs_chat:
            config.logs_chat_id = logs_chat.id
            self.logs_chat: Chat | None = logs_chat
            config.to_disk()
            return
        if not config.logs_chat_id:
            return
        try:
            __logs_chat = await client.get_chat(
                config.logs_chat_id
            )
        except:
            await self.notify(
                f'failed get logs chat {config.logs_chat_id}'
            )
            return
        if isinstance(
            __logs_chat,
            ChatPreview,
        ):
            await self.notify(
                f'got chat preview instead of logs chat {config.logs_chat_id}'
            )
        elif isinstance(
            __logs_chat,
            Chat,
        ):
            self.logs_chat = __logs_chat
        else:
            raise TypeError(
                'unexpected logs chat object type'
            )

    async def remove(
        self,
    ) -> None:
        self.logs_chat = None
        config.logs_chat_id = 0
        config.to_disk()

    async def notify(
        self,
        text: str,
        chats_list: list[int] | None = None,
        reply_markup: Ikm | None = None,
    ) -> None:
        if not reply_markup:
            reply_markup = get_buttons([['main_menu_button']], None)
        if not self.client:
            raise ValueError(
                'no client'
            )
        c.log(hl(text))
        if not chats_list:
            chats_list = config.admins.copy()
        if self.logs_chat and self.logs_chat.id not in chats_list:
            chats_list.append(self.logs_chat.id)
        for chat_id in chats_list:
            try:
                await self.client.send_message(
                    chat_id = chat_id,
                    text = text,
                    reply_markup = reply_markup,
                )
            except:
                pass

    async def log(
        self,
        text: str | None = None,
        file: str | None = None,
        to_print: bool = True,
    ) -> str:
        if not text and not file:
            raise ValueError(
                'no text and no file'
            )
        if not text:
            text = ''
        elif to_print:
            c.log(hl(text))
        if file:
            c.log(f'file: {file}')
        if not self.logs_chat:
            c.log('no logs chat')
            return ''
        if not self.client:
            c.log(hl('error: no client'))
            return ''
        msg: Message | None = None
        if file:
            try:
                msg = await self.client.send_document(
                    chat_id = self.logs_chat.id,
                    document = file,
                    caption = text,
                )
            except errors.PeerIdInvalid:
                await l.remove()
                await l.log(f'error: can not get logs chat, removing it...')
            except Exception:
                c.log(f'''
error: failed send log with file to {self.logs_chat.id}
{write_error()}
'''
                )
        else:
            try:
                msg = await self.client.send_message(
                    chat_id = self.logs_chat.id,
                    text = text,
                )
            except errors.PeerIdInvalid:
                await l.remove()
                await l.log(f'error: can not get logs chat, removing it...')
            except Exception:
                c.log(f'''
failed send log to {self.logs_chat.id}
{write_error()}
'''
                )
        if msg:
            return url(msg.chat.id) + f'/{msg.id}'
        else:
            return ''


def get_buttons(
    buttons: list[list[str]],
    user: Message | CallbackQuery | InlineQuery | User | None,
) -> Ikm:
    parsed_buttons = []
    for row in buttons:
        parsed_row = []
        for button in row:
            if button[-2:] == '_0':
                clear_button = button[:-2]
            else:
                clear_button = button
            parsed_row.append(
                Ikb(
                    text = t(
                        item = clear_button,
                        user = user,
                    ),
                    callback_data = button,
                )
            )
        parsed_buttons.append(parsed_row)
    return Ikm(parsed_buttons)


def write_error() -> str:
    max_errors_in_dir = 30
    config.errors_path.mkdir(
        exist_ok = True,
        parents = True,
    )
    all_errors = list(
        config.errors_path.iterdir()
    )
    all_errors.sort()
    while len(
        all_errors
    ) >= max_errors_in_dir:
        all_errors[0].unlink()
        all_errors.remove(all_errors[0])
    file_date = datetime.datetime.now().strftime("%Y.%m.%d_%H.%M")
    test_error_path = config.errors_path / file_date
    error_path = Path(
        f'{test_error_path}.txt'
    )
    index = 2
    while error_path.exists():
        error_path = Path(
            f'{test_error_path}_{index}.txt'
        )
        index += 1
    with open(
        error_path,
        'w',
        encoding = "utf-8",
    ) as file:
        c_error = rich.console.Console(
            width = 80,
            file = file,
        )
        c_error.print_exception(
            show_locals = False,
            suppress = [pg],
        )
    return str(error_path)


async def filter_admin(
    item: CallbackQuery | Message,
):
        
    if item.from_user.id in config.admins:
        return False
    if isinstance(
        item,
        CallbackQuery,
    ):
        await item.answer(
            text = t('denied', item)
        )
    elif isinstance(
        item,
        Message,
    ):
        await item.reply(
            text = t('denied', item)
        )
    else:
        raise TypeError('wrong item type')
    return True


def url(
    chat_id: int | str,
) -> str:
    return 't.me/c/' + str(chat_id).replace(
        '-100',
        '',
    ).replace(
        '-',
        '',
    )


def mention(
    user: User,
) -> str:
    if user.username:
        return f'@{user.username}'
    else:
        return user.mention()


def mention_nolink(
    user: User,
) -> str:
    if user.username:
        return f'@{user.username}'
    else:
        return user.first_name


async def bad_button(
    cb: CallbackQuery,
) -> None:
    await cb.answer(
        text = t('bad_button_cb', cb),
    )


async def cb_bugreport(
    cb: CallbackQuery,
    bug: str,
) -> None:
    await cb.answer(
        bug,
        show_alert = True,
    )


async def msg_bugreport(
    msg: Message,
    bug: str,
) -> None:
    await msg.reply(
        bug,
        quote = True,
    )


async def get_end_int(
    data: CallbackQuery | Message,
) -> int | None:
    if isinstance(
        data,
        CallbackQuery,
    ):
        data_str = str(data.data)
        bugreport = cb_bugreport
    elif isinstance(
        data,
        Message,
    ):
        data_str = str(chats.users_dict[data.from_user.id])
        bugreport = msg_bugreport
    end = data_str.rsplit('_', 1)[-1]
    if end.replace('-', '').isdigit():
        return int(end)
    else:
        await bugreport(
            data, # type: ignore
            f'error: got non-int "{end}" in "{data_str}"',
        )
        return


async def get_two_end_int(
    cb: CallbackQuery,
) -> list[int] | None:
    items = str(cb.data).rsplit('_', 2)[-2:]
    result = []
    for i in items:
        if not i.replace('-', '').isdigit():
            await cb.answer(
                f'error: got non-int "{i}" in "{cb.data}"',
                show_alert = True,
            )
            return
        result.append(int(i))
    return result


def hl(
    text: str,
) -> str:
    return text.replace(
        'error:',
        '[red]error:[/red]',
    ).replace(
        'success:',
        '[green]success:[/green]',
    )


chats = Chats(
    chats_path
)
l = Logs()

