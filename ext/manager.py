import json

json_path = r'./utils/'


def _load_json(name) -> dict:
    to_load = json_path + str(name).lower() + '.json' if name[-5:] != '.json' else ''
    with open(to_load) as sub:
        dct = dict(json.load(sub))
        return dct


def json_dict(name) -> dict:
    return _load_json(name=name)
