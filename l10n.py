from pathlib import Path
from typing import Set

from json import loads


class Localization:
    def __init__(self):
        core_base_dir = Path(__file__).parent.resolve()
        core_l10n_dir = core_base_dir / 'res/l10n'
        self.core_lang_list = [f.name[:-5] for f in core_l10n_dir.iterdir() if f.name.endswith('.json')]

        cust_base_dir = Path('.')
        cust_l10n_dir = cust_base_dir / 'jsons/langs'
        self.cust_lang_list = []
        if cust_l10n_dir.exists():
            self.cust_lang_list = [f.name for f in cust_l10n_dir.iterdir() if f.is_dir()]

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
                        self.l10n_dict[f]['anastellos']['info']['about']['desc'] = f_dict.get('desc', self.l10n_dict[f]['anastellos']['info']['about']['desc'])
                        self.l10n_dict[f]['anastellos']['info']['help']['commands'].update(f_dict.get('help', {}))
                        self.l10n_dict[f]['anastellos']['settings']['list'].update(f_dict.get('settings_list', {}))
                        self.l10n_dict[f]['cmds'] = f_dict.get('cmds', {})
                    elif f_path.name == 'privacy.json':
                        self.l10n_dict[f]['privacy'] = f_dict

    def getlang(self, lang: str) -> dict:
        return self.l10n_dict[lang]
    
    @property
    def lang_list(self) -> Set[str]:
        return set(self.core_lang_list + self.cust_lang_list)