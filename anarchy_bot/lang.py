# license is gnu agpl 3 - gnu.org/licenses/agpl-3.0.en.html

from pathlib import Path
from pyrogram.types import (
    CallbackQuery,
    InlineQuery,
    Message,
    User,
)
from config import (
    src_path,
    yml,
    c,
)


class TranslationError(Exception):
    pass


class Translation:
    def __init__(
            self,
            path: str | Path = f'{src_path}/lang',
            warns: bool = True,
        ) -> None:
        self.data = {}
        self.path = Path(path)
        self.warns = warns
        for file in Path(path).iterdir():
            self.data[file.stem] = yml.from_file(
                file
            )

    def translate(
        self,
        item: str,
        user: User | Message | InlineQuery | CallbackQuery | None,
    ) -> str:
        lang = 'en'
        if isinstance(
            user,
            User,
        ):
            lang = user.language_code
        for i in (
            Message,
            InlineQuery,
            CallbackQuery,
        ):
            if isinstance(
                user,
                i,
            ):
                try:
                    lang = user.from_user.language_code
                except Exception:
                    lang = 'en'
        if not lang:
            lang = 'en'
        if 'en' not in self.data:
            raise TranslationError(
                f'en not in {self.path}'
            )
        if item not in self.data['en']:
            raise TranslationError(
                f'{item} not in en'
            )
        if self.warns:
            if lang not in self.data:
                c.log(f'[yellow]warn:[/yellow] {lang} not in [deep_sky_blue1]{self.path}')
            elif item not in self.data[lang]:
                c.log(f'[yellow]warn:[/yellow] not in {lang}')
            lang = 'en'
        return self.data[lang][item].strip(
            '"""'
        ).strip(
            '"""\n'
        )


translation = Translation()
t = translation.translate

