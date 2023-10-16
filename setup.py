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
activate_sh = venv_path / 'bin' / 'activate'
venv_python = venv_path / 'bin' / 'python'
start_sh = app_path / 'start.sh'
ssh_ip = '141.145.194.71'
ssh_username = 'bogdan'
pip = [
    venv_python,
    '-m',
    'pip',
]
dependencies = [
    'gmanka_yml==23.0.*',
    'pyrogram==2.0.*',
    'tgcrypto==1.2.*',
    'uvloop==0.17.*',
    'rich==13.4.*',
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

    venv.create(venv_path)
    get_pip_url = 'https://bootstrap.pypa.io/get-pip.py'
    response = urllib.request.urlopen(
        get_pip_url
    )
    total_size = int(
        response.headers.get('content-length', 0)
    )
    block_size = 1024 * 8
    count = 0
    get_pip = b''
    while True:
        chunk = response.read(block_size)
        if not chunk:
            break
        get_pip += chunk
        count += 1
        done = count * block_size
        percent_done = done * 100 // total_size
        print(
            f'\rdownloading get-pip.py: {percent_done}%',
            end = '',
        )
        sys.stdout.flush()
    print()
    python_process = subprocess.Popen(
        [venv_python],
        stdin = subprocess.PIPE,
    )
    python_process.communicate(
        input = get_pip
    )
    subprocess.run(
        [*pip, 'install', '-U', *dependencies]
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

