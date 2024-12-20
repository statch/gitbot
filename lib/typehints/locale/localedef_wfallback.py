# coding: utf-8

try:
    from resources.gen.locale_schema import Locale as LocaleDictProxyDef
except ImportError:
    from lib.structs.proxies.dict_proxy import DictProxy
    LocaleDictProxyDef = DictProxy

__all__: tuple = ('LocaleDictProxyDef',)
