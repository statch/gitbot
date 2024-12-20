# coding: utf-8

from lib.structs.proxies.dict_proxy import DictProxy

try:
    from resources.gen.locale_schema import Locale as LocaleDictProxyDef
except ImportError:
    LocaleDictProxyDef = DictProxy

try:
    from resources.gen.env_defaults_schema import EnvDefaults as EnvDefaultsProxyDef
except ImportError:
    EnvDefaultsProxyDef = DictProxy


__all__: tuple = ('LocaleDictProxyDef', 'EnvDefaultsProxyDef')
