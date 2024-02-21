#!/bin/python3
# license is gnu agpl 3 - gnu.org/licenses/agpl-3.0.en.html

from pathlib import Path
import urllib.request
import subprocess
import shutil
import venv
import sys


setup_py = Path(
    __file__
)
app_name = 'anarchy_bot'
app_path = Path(
    __file__
).parent.resolve()
venv_path = app_path / '.venv'
venv_bin = venv_path / 'bin'
activate_sh = venv_bin / 'activate'
venv_python = venv_bin / 'python'
pip = venv_bin / 'pip'
start_sh = app_path / 'start.sh'
dependencies = [
    'gmanka_yml',
    'pyrogram',
    'tgcrypto',
    'uvloop',
    'rich',
]


def green(
    text: str,
):
    return '\033[1;32m' + text + '\033[0m'

def red(
    text: str,
):
    return '\033[1;31m' + text + '\033[0m'


def install_libs():
    if venv_path.exists():
        shutil.rmtree(venv_path)

    venv.create(
        env_dir = venv_path,
        with_pip = True,
    )
    subprocess.run(
        [pip, 'install', '-U', 'pip']
    )
    subprocess.run(
        [pip, 'install', '-U', *dependencies]
    )


def main():
    install_libs()

    start_sh.write_text(
f'''\
#!/bin/bash
{venv_python} {app_name}
\n'''
    )
    start_sh.chmod(0o755)
    setup_py.chmod(0o755)
    print(green(
        'successfuly installed, use ./start.sh to start'
    ))


if __name__ == '__main__':
    main()

