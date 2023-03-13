import logging
from collections.abc import MutableMapping
from json import loads
from pathlib import Path
from typing import Optional, Set, Union

_log = logging.getLogger(__name__)


class Localization:
    def __init__(self):
        core_base_dir = Path(__file__).parent.resolve()
        core_l10n_dir = core_base_dir / 'res/l10n'
        self.core_lang_list = [f.name[:-5] for f in core_l10n_dir.iterdir() if f.name.endswith('.json') and not f.name.startswith('_')]

        cust_base_dir = Path('.')
        cust_l10n_dir = cust_base_dir / 'jsons/langs'
        self.cust_lang_list = []
        if cust_l10n_dir.exists():
            self.cust_lang_list = [f.name for f in cust_l10n_dir.iterdir() if f.is_dir() and not f.name.startswith('_')]

        self.l10n_dict = {}
        for f in self.core_lang_list:
            f_path = core_l10n_dir / (f + '.json')
            with open(f_path, 'rb') as f_file:
                self.l10n_dict[f] = loads(f_file.read())
        for f in self.cust_lang_list:
            f_paths = cust_l10n_dir / f
            for f_path in f_paths.iterdir():
                with open(f_path, 'rb') as f_file:
                    f_dict = loads(f_file.read())
                    if f_path.name == 'custom.json':
                        self.l10n_dict[f]['anastellos']['cogs']['info']['commands']['about']['desc'] = f_dict.get('desc', self.l10n_dict[f]['anastellos']['cogs']['info']['commands']['about']['desc'])
                        self.l10n_dict[f]['anastellos']['help']['commands'].update(f_dict.get('help', {}))
                        self.l10n_dict[f]['anastellos']['cogs']['settings']['list'].update(f_dict.get('settings_list', {}))
                        self.l10n_dict[f]['cmds'] = f_dict.get('cmds', {})
                    elif f_path.name == 'privacy.json':
                        self.l10n_dict[f]['privacy'] = f_dict

    def getlang(self, lang: str):
        return PartialL10n(lang, self.l10n_dict[lang])

    @property
    def lang_list(self) -> Set[str]:
        return set(self.core_lang_list + self.cust_lang_list)


class PartialL10n(MutableMapping):
    def __init__(self, part_str: str = "", part_dict: Optional[Union[dict, list, str]] = {}):
        self.store = {}
        if isinstance(part_dict, dict):
            self.update(part_dict)
        elif isinstance(part_dict, list):
            self.store = {'_list': part_dict}
        elif isinstance(part_dict, (str, int)):
            self.store = {'_str': part_dict}
        self.part_str = part_str

    def __getitem__(self, key):
        item = None
        if '_list' in self.store and isinstance(key, int):
            try:
                item = self.store['_list'][key]
            except:
                pass
        elif '_str' in self.store and isinstance(key, int):
            try:
                item = self.store['_str'][key]
            except:
                pass
        else:
            item = self.store.get(key)
        if item is None:
            item = PartialL10n(self.part_str + '.' + str(key))
        # elif isinstance(item, dict):
        #     item = PartialL10nDict(self.part_str + '.' + key, item)
        # elif isinstance(item, list):
        #     item = PartialL10nList()
        # elif isinstance(item, str):
        #     item = PartialL10nStr(item, self.part_str)
        else:
            item = PartialL10n(self.part_str + '.' + str(key), item)
        return item

    def get(self, key, default=None):
        return self.__getitem__(key)

    def __setitem__(self, key, value):
        self.store[key] = value

    def __delitem__(self, key):
        del self.store[key]

    def __iter__(self):
        return iter(self.store)

    def __len__(self):
        return len(self.store)

    def __str__(self) -> str:
        if '_str' in self.store:
            return str(self.store['_str'])
        if not self.store:
            return self.part_str
        else:
            return super().__str__()

    def __int__(self):
        if '_str' in self.store:
            return int(self.store['_str'])
        else:
            return 0
    def format(self, *args, **kwargs):
        return self.__str__().format(*args, **kwargs)

    def __add__(self, other):
        if isinstance(other, str) and '_str' in self.store:
            return self.store['_str'] + other
        else:
            return self.part_str

    # def getstr(self, l10nstr: str) -> Union[dict, str]:
    #     l10ndiv = l10nstr.split('.')
    #     cur_l10n = self.getlang()
    #     for div in l10ndiv:
    #         pass
    #     # self.getstr()
    #     _log.debug('partloc getstr')