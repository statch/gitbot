# coding: utf-8

from lib.structs.proxies.dict_proxy import DictProxy
from lib.structs.proxies.dir_proxy import DirProxy

try:
    from resources.gen.locale_schema import Locale as LocaleDictProxyDef
except ImportError:
    LocaleDictProxyDef = DictProxy

try:
    from resources.gen.gql_queries_schema import GraphQLQueries as GraphQLQueriesDirProxyDef
except ImportError:
    GraphQLQueriesDirProxyDef = DirProxy


__all__: tuple = ('LocaleDictProxyDef', 'GraphQLQueriesDirProxyDef')
