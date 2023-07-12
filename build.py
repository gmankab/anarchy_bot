#!/bin/python

from pathlib import Path
import shutil
import toml
import os
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
        'description': 'telegram bot that can add users to minecraft whitelist',
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
os.system('python -m hatchling build')
for file in dist_path.iterdir():
    if file.suffix != '.whl':
        file.unlink()
os.system('python -m prettygit')

