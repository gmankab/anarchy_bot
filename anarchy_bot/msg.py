import pyrogram as pg
import pyrogram.enums
import pyrogram.errors
from lang import t
from pyrogram.client import Client
from pyrogram.types import (
    ChatPrivileges,
    ChatMember,
    Message,
)
from config import(
    yes_no,
    config,
    c,
)
from common import (
    filter_admin,
    write_error,
    get_buttons,
    mention,
    chats,
    l,
)
from chats import (
    ask_to_set_logs_chat_msg,
    notify_removed,
    setlogs_msg,
)


c.log(f'imported [deep_sky_blue1]{__file__}')


async def catched_on_message(
    client: Client,
    msg: Message,
):
    try:
        await on_message(
            client,
            msg,
        )
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
    if not config.owner:
        await set_owner(
            msg,
        )
    if msg.chat.type == pg.enums.ChatType.PRIVATE:
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
    client: Client,
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


async def becomeadmin(
    client: Client,
    msg: Message,
):
    splitted = msg.text.split(' ', 1)
    if len(splitted) == 1:
        await msg.reply(
            'you must specify your title after /becomeadmin\n\nexample: /becomeadmin bebra'
        )
        return
    title = splitted[-1][:16]
    if msg.chat.type != pyrogram.enums.ChatType.SUPERGROUP:
        await msg.reply(
            'wrong chat type, expected supergroup, got ' + str(msg.chat.type).lower()
        )
        return
    if not msg.from_user:
        await msg.reply(
            'you must send message as user, not as channel or chat'
        )
    text = f'trying to make {mention(msg.from_user)} an admin...'
    responce: Message = await msg.reply(
        text
    )
    while True:
        try:
            await client.promote_chat_member(
                chat_id = msg.chat.id,
                user_id = msg.from_user.id,
                privileges = ChatPrivileges(
                    can_manage_chat = True,
                    can_change_info = True,
                ),
            )
            text += f'\n\nsuccesfully promoted {mention(msg.from_user)} to admin'
            await responce.edit_text(text)
            break
        except pyrogram.errors.ChatAdminRequired:
            text += '\n\ni have no rights to make you an admin'
            await responce.edit_text(text)
            return
        except pyrogram.errors.UserCreator:
            text += '\n\nbro you are chat owner'
            await responce.edit_text(text)
            return
        except pyrogram.errors.AdminsTooMuch:
            admins: list[ChatMember] = await chats.list_chat_admins(
                client = client,
                chat = msg.chat,
            )
            demoted = False
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
                    demoted = True
                    text += f'\n\ntoo many admins, demoting {mention(admin.user)}'
                    await responce.edit_text(text)
                    break
                except pyrogram.errors.UserCreator:
                    continue
                except Exception as e:
                    text += f'\n\nfailed to demote {mention(admin.user)}\n{e}'
                    await responce.edit_text(text)
                    continue
            if demoted:
                break
            text += f'\n\ntoo many admins, no admin available to demote'
            await responce.edit_text(text)
            return
    await client.set_administrator_title(
        chat_id = msg.chat.id,
        user_id = msg.from_user.id,
        title = title,
    )
    text += f'\n\nsuccesfully set title {title}'
    await responce.edit_text(text)


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

