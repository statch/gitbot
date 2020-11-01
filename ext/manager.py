import json
from fuzzywuzzy import fuzz


json_path = r'./utils/'


def _load_json(name: str):
    to_load = json_path + str(name).lower() + '.json' if name[-5:] != '.json' else ''
    with open(to_load) as sub:
        dct = json.load(sub)
        return dct


def json_dict(name: str):
    return _load_json(name=name)


class Manager:
    def __init__(self):
        self.licenses = json_dict("licenses")
        self.emojis = json_dict("emoji")

    def correlate_license(self, to_match: str) -> dict or None:
        for i in [x for x in self.licenses]:
            match = fuzz.token_set_ratio(to_match, i["name"])
            if match >= 80:
                return [y for y in self.licenses if y["name"] == i["name"]][0]
            match1 = fuzz.token_set_ratio(to_match, i["key"])
            if match1 >= 80:
                return [y for y in self.licenses if y["key"] == i["key"]][0]
            match2 = fuzz.token_set_ratio(to_match, i["spdx_id"])
            if match2 >= 80:
                return [y for y in self.licenses if y["spdx_id"] == i["spdx_id"]][0]
        return None
