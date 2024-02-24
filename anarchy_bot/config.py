# license is gnu agpl 3 - gnu.org/licenses/agpl-3.0.en.html

from pyrogram.client import Client
from pathlib import Path
from typing import Any
import pyrogram as pg
import gmanka_yml as yml
import rich.console
import platform
from pyrogram.types import(
    User,
)


try:
    import uvloop
    uvloop_version = uvloop._version.__version__
except Exception:
    uvloop_version = None
try:
    import tgcrypto # type: ignore
    using_tgcrypto = True
except Exception:
    using_tgcrypto = False


app_name = 'anarchy_bot'
app_version = '24.1.9'
c = rich.console.Console()
app_path = Path(
    __file__
).parent.parent.resolve()
src_path = app_path / app_name
data_path = app_path / f'{app_name}_data'
wl_path = data_path / 'whitelist.yml'
chats_path = data_path / 'chats.yml'

os_name = platform.system()
if os_name == 'Linux':
    try:
        os_name = platform.freedesktop_os_release()['PRETTY_NAME']
    except Exception:
        pass


start_message = f'''\
gmanka {app_name} {app_version}
pyrogram {pg.__version__}
uvloop {uvloop_version}
tgcrypto {using_tgcrypto}
{platform.python_implementation()} {platform.python_version()}
{os_name} {platform.release()}
data path: `{data_path}`\
'''


def get(
    data: dict,
    item: str,
    default: Any,
    expected_type: Any,
) -> Any:
    got = data.get(
        item,
        default,
    )
    if isinstance(
        got,
        expected_type,
    ):
        return got
    else:
        return default
        

def yes_no(
    to_print: str
) -> bool:
    c.print(
        to_print,
        end = '',
    )
    yes_no = input()
    if yes_no in [
        '',
        'Y',
        'y',
    ]:
        return True
    else:
        return False


def interactive_input(
    to_print: str
) -> str:
    while True:
        c.print(
            to_print,
            end = '',
        )
        data = input()
        if data:
            if yes_no(
                f'[deep_sky_blue1]{data}[/deep_sky_blue1] - is it correct? [Y/n] ',
            ):
                return data


class Config:
    def __init__(
        self,
        data_path: Path,
    ) -> None:
        self.data_path:Path = data_path
        self.config_path: Path = data_path / f'{app_name}.yml'
        self.errors_path: Path = self.data_path / 'errors'
        self.page_size = 5
        data: dict = yml.from_file( # type: ignore
            path = self.config_path,
            default = {},
            expected_type = dict,
        )
        self.owner: int = get(
            data = data,
            item = 'owner',
            default = 0,
            expected_type = int,
        )
        self.logs_chat_id: int = get(
            data = data,
            item = 'logs_chat_id',
            default = 0,
            expected_type = int,
        )
        self.admins: list[int] = get(
            data = data,
            item = 'admins',
            default = [],
            expected_type = list,
        )
        self.session: str = get(
            data = data,
            item = 'session',
            default = '',
            expected_type = str,
        )
        self.token: str | None = get(
            data = data,
            item = 'token',
            default = '',
            expected_type = str | None,
        )
        if self.owner and self.owner not in self.admins:
            self.admins.append(self.owner)
        self.__me: User | None = None
    def __get_me(self) -> User:
        if self.__me == None:
            raise ValueError('me was not set')
        return self.__me

    async def init(
        self,
        client: Client,
    ) -> None:
        if not self.__me:
            self.__me = await client.get_me()

    def to_disk(
        self,
    ) -> None:
        if not self.config_path:
            c.log('[red] not writed because path not specified')
            return
        self.config_path.parent.mkdir(
            parents = True,
            exist_ok = True,
        )
        yml.to_file(
            data = {
                'version': app_version,
                'logs_chat_id': self.logs_chat_id,
                'admins': self.admins,
                'owner': self.owner,
                'token': self.token,
                'session': self.session,
            },
            path = self.config_path,
        )
        c.log(f'success: writed changes to [deep_sky_blue1]{self.config_path}')

    me: User = property(fget = __get_me) # type: ignore


config = Config(
    data_path = data_path,
)

