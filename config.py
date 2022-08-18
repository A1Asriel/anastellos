import json
from os import listdir

from .exceptions import AnastellosInitError
from .utils import get_config


class SimpleConfig:
    def __init__(self, filename: str, **kwargs):
        self._def_schema = {}
        self._schema = self._def_schema
        self._filename = filename
        for arg, value in kwargs.items():
            self.__setattr__(arg, value)

    def __assignattrs__(self):
        try:
            cfg = get_config(filename=self._filename, schema=self._schema)
        except json.JSONDecodeError:
            cfg = self._schema
            print('[WARN] Using the default config.')
        for key in self._def_schema.keys():
            self.__setattr__(key, cfg[key])

    def __compileschema__(self):
        self._schema = {key: self.__getattribute__(key) for key in self._def_schema.keys()}
    
    def __resetschema__(self):
        self._schema = self._def_schema

    def save(self):
        with open(self._filename, 'w', encoding="utf-8") as f:
            json.dump(self._schema, f, indent=4, ensure_ascii=False)

class Config(SimpleConfig):
    def __init__(self, filename: str = 'cfg', *, additional_guild_params: dict[str] = {}, **kwargs):
        super().__init__(filename, **kwargs)

        self.__settings = ('name', 'stage', 'mode', 'version', 'def_prefix', 'owner', 'anastellos_logo')

        self.name: str = 'Anastellos Engine'
        self.stage = 'Release'
        self.mode = 'normal'
        self.version = '1.0'
        self.def_prefix = 'ae!'
        self.owner = 0
        self.anastellos_logo = 'https://cdn.discordapp.com/attachments/713481949896900622/992450921852313640/anastellos_engine_logo.png'

        self._def_schema = {name: self.__getattribute__(name) for name in self.__settings}
        self._schema = self._def_schema

        self.__assignattrs__()
        self.__compileschema__()

        self.self_avatar_url = ''
        self._langfiles_path = 'jsons/langs/'
        self._def_guild_config = {
            "prefix": self.def_prefix,
            "lang": "en"
        }
        self.build = '1.0.0.1'
        self.additional_guild_params = additional_guild_params
        self._def_guild_config.update(self.additional_guild_params)

        langfiles = listdir(self._langfiles_path)
        self.lang_names = set()
        for langn in langfiles:
            if langn.startswith(('ign_', '__')):
                continue
            self.lang_names.add(langn.removesuffix('.json'))
        if not self.lang_names:
            print('[FATAL] No localization files found. The bot is unable to initialize.')
            raise AnastellosInitError(__stage__='config')

        for arg, value in kwargs.items():
            self.__setattr__(arg, value)

    def save(self):
        with open(self._filename, 'w', encoding="utf-8") as f:
            json.dump()

    @property
    def full_version(self):
        return f'{self.stage} {self.version} [{self.build}]'
