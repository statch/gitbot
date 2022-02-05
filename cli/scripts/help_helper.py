import os
import json
import click
import atexit
import copy
from typing import Optional
from collections import OrderedDict
from cli.config import APP_ROOT_DIR
from .common import get_master_locale, save_changes

__all__: tuple = ('run_help_helper', 'PROMPTS')
# We use these ugly-ish type annotations since we can't annotate global variables
DEBUG = False  # type: bool
OLD_LOCALE = None  # type: Optional[OrderedDict]
LOCALE = None  # type: Optional[OrderedDict]
PROMPTS = OrderedDict([('brief', lambda: click.prompt(f'Brief', type=str)),
                       ('description', lambda: click.prompt(f'Description', type=str, default='skip')),
                       ('usage', lambda: click.prompt(f'Usage', type=str, default='skip')),
                       ('example', lambda: click.prompt(f'Example', type=str, default='skip')),
                       ('qa_resource', lambda: click.prompt(f'Quick-Access Resource',
                                                            type=click.Choice(['user', 'org', 'repo', 'skip'],
                                                                              case_sensitive=False), default='skip')),
                       ('required_permissions', lambda: [rp.strip() for rp in
                                                         click.prompt(f'Required Permissions',
                                                                      type=str, default='skip').split(',')])])


def fix_dict(d: OrderedDict) -> OrderedDict:
    for k, v in d.items():
        if isinstance(v, str) and v.lower() == 'skip':
            d[k] = None
        elif isinstance(v, list) and 'skip' in v:
            d[k] = []
    return d


def exit_save_changes() -> None:
    global LOCALE, OLD_LOCALE

    if LOCALE and OLD_LOCALE and LOCALE != OLD_LOCALE:
        if not DEBUG:
            save_changes(LOCALE, OLD_LOCALE)
            click.echo(click.style('Changes saved.', fg='green'))
        else:
            click.echo(click.style('Exit-save callback would be called,'
                                   ' but debug mode is enabled.', fg='yellow', italic=True))


def prompt(name: str, is_group: bool) -> OrderedDict:
    term: str = "command" if not is_group else "group"
    click.echo(click.style(f'{term.title()}: {name}', fg='bright_cyan'))
    prompt_results: dict = {vn: p() for vn, p in PROMPTS.items()}
    ret = OrderedDict([('brief', ''),
                       ('usage', None),
                       ('example', None),
                       ('description', None),
                       ('qa_resource', None),
                       ('required_permissions', [])])
    ret.update(prompt_results)
    return fix_dict(ret)


def run_help_helper(debug: bool = False):
    global LOCALE, OLD_LOCALE, DEBUG

    atexit.register(exit_save_changes)
    DEBUG = debug
    if debug:
        click.echo(click.style('Debug mode enabled.', fg='yellow', italic=True))

    try:
        with open(os.path.join(APP_ROOT_DIR, 'commands.json'), 'r') as command_file:
            raw_command_list_json: str = command_file.read()
            commands: list[str] = json.loads(raw_command_list_json)
    except FileNotFoundError:
        click.echo(click.style('Could not find commands.json!'
                               ' Generate it with "git dev export-commands json" via Discord', fg='bright_red'))
        return
    LOCALE = get_master_locale()
    OLD_LOCALE = copy.deepcopy(LOCALE)

    processed: list[str] = []

    for command_name in commands:
        underscored_name: str = command_name.replace(' ', '_')
        if underscored_name not in LOCALE['help']['commands']:
            command_data = prompt(command_name,
                                  is_group=(raw_command_list_json.count('"' + command_name + ' ') > 1
                                            and ' ' not in command_name))
            while True:
                if click.confirm(click.style(f'All good?', blink=True, fg='yellow') + '\n' +
                                 '\n'.join([click.style(f'{k}: {v}', fg='cyan')
                                            for k, v in command_data.items()]) + ' |',
                                 default=True, show_default=True):
                    LOCALE['help']['commands'][underscored_name] = command_data
                    break
                else:
                    to_correct = click.prompt(click.style('What do you wish to correct? ("nevermind" to skip)',
                                                          fg='yellow'),
                                              type=click.Choice([*PROMPTS.keys(), 'nevermind'], case_sensitive=False))
                    if to_correct == 'nevermind':
                        LOCALE['help']['commands'][underscored_name] = command_data
                        break
                    command_data[to_correct] = PROMPTS[to_correct]()
                    fix_dict(command_data)
            try:
                if (not click.confirm(click.style(f'Do you wish to add another command?'
                                                  f' (Next up: {commands[commands.index(command_name) + 1]})',
                                                  blink=True, fg='bright_cyan'),
                                      default=True, show_default=True)) or command_name == commands[-1]:
                    break
            except IndexError:
                pass
        else:
            click.echo(click.style(f'Skipping command/group {command_name} - already added', fg='cyan'))
        processed.append(command_name)
    if len(commands) - len(processed) == 0:
        click.echo(click.style('🎉 All done! 🎉', fg='bright_magenta', bold=True, underline=True))
    else:
        click.echo(click.style(f'Solid work, {len(commands) - len(processed)} commands left for next time!',
                               fg='bright_magenta'))
