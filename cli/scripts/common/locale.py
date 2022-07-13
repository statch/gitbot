import os
import json
from collections import OrderedDict
from cli.config import INDEX_LOCALE_FILE, LOCALE_DIR

__all__: tuple = ('get_master_locale', 'save_changes')


def get_master_locale() -> OrderedDict:
    with open(INDEX_LOCALE_FILE, 'r', encoding='utf8') as index_locale_file:
        locale_index: dict = json.load(index_locale_file)
    with open(os.path.join(LOCALE_DIR, f'{locale_index["master"]}.locale.json'), 'r', encoding='utf8') as locale_file:
        return json.load(locale_file, object_pairs_hook=OrderedDict)  # noqa, we use OrderedDict to be safe


def save_changes(updated: OrderedDict, old: OrderedDict) -> None:
    if updated != old:
        with open(os.path.join(LOCALE_DIR, f'{old["meta"]["name"]}.locale.last.json'),
                  'w+', encoding='utf8') as old_locale_file:
            old_locale_file.write(json.dumps(old, indent=2))
        with open(os.path.join(LOCALE_DIR, f'{updated["meta"]["name"]}.locale.json'),
                  'w+', encoding='utf8') as locale_file:
            locale_file.write(json.dumps(updated, indent=2))
