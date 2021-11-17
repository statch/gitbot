import os
import sys
import click
import subprocess

APP_ROOT_DIR: str = (CLI_ROOT_DIR := os.path.dirname((os.path.abspath(__file__))))[:CLI_ROOT_DIR.rindex(os.sep)]
PYTHON_COMMAND_LINE: str = (os.path.join(APP_ROOT_DIR, 'venv/Scripts/python.exe') if
                            'venv' in os.listdir(APP_ROOT_DIR) else (sys.executable or 'python'))


@click.group()
def cli():
    pass


@cli.group('bot', help='Commands related to running and maintaining the bot')
def bot():
    pass


@bot.command('start', help='Start the bot using launcher.py')
@click.option('--no-new-window',
              is_flag=True, help='Don\'t start the bot in a new terminal window, even if possible', default=False)
def start(no_new_window: bool = False):
    if sys.platform == 'win32' and not no_new_window:
        subprocess.call(f'start {PYTHON_COMMAND_LINE} launcher.py', shell=True)
    else:
        subprocess.call([PYTHON_COMMAND_LINE, 'launcher.py'])


@cli.group('dev', help='Commands related to the development of the bot')
def dev():
    pass


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
