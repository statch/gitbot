import os
import sys

__all__: tuple = ('APP_ROOT_DIR', 'PYTHON_COMMAND_LINE', 'LOCALE_DIR', 'INDEX_LOCALE_FILE')

APP_ROOT_DIR: str = (CLI_ROOT_DIR := os.path.dirname((os.path.abspath(__file__))))[:CLI_ROOT_DIR.rindex(os.sep)]
PYTHON_COMMAND_LINE: str = (os.path.join(APP_ROOT_DIR, 'venv/Scripts/python.exe') if
                            'venv' in os.listdir(APP_ROOT_DIR) else (sys.executable or 'python'))
LOCALE_DIR: str = os.path.join(APP_ROOT_DIR, 'resources/locale')
INDEX_LOCALE_FILE: str = os.path.join(LOCALE_DIR, 'index.json')
