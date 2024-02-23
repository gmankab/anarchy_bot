#!/bin/python
# license is gnu agpl 3 - gnu.org/licenses/agpl-3.0.en.html

from pathlib import Path
import subprocess
import shutil
import toml
import sys
from setup import (
    app_name,
)
from anarchy_bot.config import (
    app_version,
)
from setup import (
    dependencies,
    app_name,
)


app_path = Path(
    __file__
).parent.resolve()
pypr_path = app_path / 'pyproject.toml'
dist_path = app_path / 'dist'
description = 'true anarchy in telegram chats'

pypr_data = {
    'build-system': {
        'requires': ['hatchling'],
        'build-backend': 'hatchling.build',
    },
    'project': {
        'dependencies': dependencies,
        'name': app_name,
        'version': app_version,
        'authors': [
            {
                'name': 'gmanka',
                'email': 'gmankab@gmail.com',
            },
        ],
        'description': description,
        'readme': 'readme.md',
        'requires-python': '>=3.10',
        'classifiers': [
            'Programming Language :: Python :: 3',
            'Operating System :: OS Independent',
        ],
        'urls': {
            'Documentation': 'https://t.me/gmanka',
            'Bug Tracker': 'https://t.me/gmanka',
            'Homepage': 'https://t.me/gmanka',
        }
    }
} 


with open(
    pypr_path,
    'w',
) as file:
    file.write(
        toml.dumps(
            pypr_data
        )
    )

shutil.rmtree(
    dist_path,
    ignore_errors = True,
)
subprocess.run(
    [sys.executable, '-m', 'hatchling', 'build'],
    check=True,
)
subprocess.run(
    [sys.executable, '-m', 'twine', 'upload', 'dist/*'],
    check=True,
)

