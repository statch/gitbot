import os
import sys
import click
import typeshi
import subprocess
from lib.structs.proxies.dict_proxy import DictProxy
from .config import PYTHON_COMMAND_LINE, APP_ROOT_DIR
from .scripts import run_help_helper


@click.group()
def cli():
    pass


@cli.group('bot', help='Commands related to running and maintaining the bot')
def bot():
    pass


@bot.command('start', help='Start the bot using bot.py')
@click.option('--no-new-window',
              is_flag=True, help='Don\'t start the bot in a new terminal window, even if possible', default=False)
def start(no_new_window: bool = False):
    if sys.platform == 'win32' and not no_new_window:
        subprocess.call(f'start {PYTHON_COMMAND_LINE} bot.py', shell=True)
    else:
        subprocess.call([PYTHON_COMMAND_LINE, 'bot.py'])


@cli.group('dev', help='Commands related to the development of the bot')
def dev():
    pass


@dev.command('generate-locale-defs')
def generate_locale_defs():
    if not os.path.exists('resources/gen/'):
        os.makedirs('resources/gen/')
    typeshi.save_declaration_module_from_json(
        'Locale', 'resources/locale/en.locale.json', 'resources/gen/locale_schema.py',
        inherit_cls=DictProxy
    )
    print(f'Wrote locale schema to resources/gen/locale_schema.py')


@dev.command('update', help='Update the local code using git')
def update():
    if sys.platform == 'win32':
        subprocess.call('git pull', shell=True)
    else:
        subprocess.call(['git', 'pull'])


@dev.command('install', help='Install the dependencies using pip')
def install():
    path: str = os.path.abspath(os.path.join(APP_ROOT_DIR, 'requirements.txt'))
    if sys.platform == 'win32':
        subprocess.call(f'{PYTHON_COMMAND_LINE} -m pip install --disable-pip-version-check -r {path}', shell=True)
    else:
        subprocess.call([PYTHON_COMMAND_LINE, '-m', 'pip', 'install', '--disable-pip-version-check', '-r', path])


@dev.command('help-helper',
             help='Incredibly useful command with an even more incredibly hilarious name that displays prompts '
                  'for each command that needs to have its help added into the default locale file. Before using this, '
                  'use the "git dev export-commands json" command, so that the script has a command list to work with')
@click.option('--debug', is_flag=True,
              help='Does not actually update the locale files, useful for updating this command itself', default=False)
def help_helper(debug: bool = False):
    run_help_helper(debug=debug)
