import os
import json
import click
import atexit
import copy
from typing import Optional
from collections import OrderedDict
from cli.config import APP_ROOT_DIR, LOCALE_DIR

__all__: tuple = ('run_help_helper',)
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
                       ('argument_explainers', lambda: [ae.strip() for ae in
                                                        click.prompt(f'Argument Explainers',
                                                                     type=str, default='skip').split(',')]),
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


def exit_save_changes(unregister_atexit: bool = True) -> None:
    global LOCALE, OLD_LOCALE

    if LOCALE and OLD_LOCALE and LOCALE != OLD_LOCALE:
        if not DEBUG:
            if unregister_atexit:
                atexit.unregister(exit_save_changes)
            with open(os.path.join(LOCALE_DIR, f'{LOCALE["meta"]["name"]}.last.json'), 'w+') as old_locale_file:
                old_locale_file.write(json.dumps(OLD_LOCALE, indent=2))
            with open(os.path.join(LOCALE_DIR, f'{LOCALE["meta"]["name"]}.json'), 'w+') as locale_file:
                locale_file.write(json.dumps(LOCALE, indent=2))
            click.echo(click.style('Changes saved.', fg='green'))
        else:
            click.echo(click.style('Exit-save callback would be called,'
                                   ' but debug mode is enabled.', fg='yellow', italic=True))


atexit.register(exit_save_changes)


def prompt(name: str, is_group: bool) -> OrderedDict:
    term: str = "command" if not is_group else "group"
    click.echo(click.style(f'{term.title()}: {name}', fg='bright_cyan'))
    underscored_name: str = name.replace(' ', '_')
    prompt_results: dict = {vn: p() for vn, p in PROMPTS.items()}
    ret = OrderedDict([('underscored_name', underscored_name),
                       ('brief', ''),
                       ('usage', None),
                       ('example', None),
                       ('description', None),
                       ('argument_explainers', []),
                       ('qa_resource', None),
                       ('required_permissions', [])])
    ret.update(prompt_results)
    return fix_dict(ret)


def run_help_helper(debug: bool = False):
    global LOCALE, OLD_LOCALE, DEBUG

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
    with open(os.path.join(LOCALE_DIR, 'index.json'), 'r') as locale_index_file:
        locale_index: dict = json.load(locale_index_file)
    with open(os.path.join(LOCALE_DIR, f'{locale_index["master"]}.json'), 'r') as locale_file:
        LOCALE = json.load(locale_file, object_pairs_hook=OrderedDict)  # noqa, we use OrderedDict to be safe
        OLD_LOCALE = copy.deepcopy(LOCALE)

    processed: list[str] = []

    for command_name in commands:
        if command_name not in LOCALE['help']['commands']:
            command_data = prompt(command_name,
                                  is_group=(raw_command_list_json.count('"' + command_name + ' ') > 1
                                            and ' ' not in command_name))
            while True:
                if click.confirm(click.style(f'All good?', blink=True, fg='yellow') + '\n' +
                                 '\n'.join([click.style(f'{k}: {v}', fg='cyan')
                                            for k, v in command_data.items()]) + ' |',
                                 default=True, show_default=True):
                    LOCALE['help']['commands'][command_data.pop('underscored_name')] = command_data
                    break
                else:
                    to_correct = click.prompt(click.style('What do you wish to correct? ("nevermind" to skip)',
                                                          fg='yellow'),
                                              type=click.Choice([*PROMPTS.keys(), 'nevermind'], case_sensitive=False))
                    if to_correct == 'nevermind':
                        break
                    command_data[to_correct] = PROMPTS[to_correct]()
                    fix_dict(command_data)
            if (not click.confirm(click.style(f'Do you wish to add another command?'
                                              f' (Next up: {commands[commands.index(command_name) + 1]})',
                                              blink=True, fg='bright_cyan'),
                                  default=True, show_default=True)) or command_name == commands[-1]:
                exit_save_changes()
                break
        else:
            click.echo(click.style(f'Skipping command/group {command_name} - already added', fg='cyan'))
        processed.append(command_name)
    if len(commands) - len(processed) == 0:
        click.echo(click.style('🎉 All done! 🎉', fg='bright_magenta', bold=True, underline=True))
    else:
        click.echo(click.style(f'Solid work, {len(commands) - len(processed)} commands left for next time!',
                               fg='bright_magenta'))
