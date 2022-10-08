from __future__ import annotations

import json
import logging
from os import listdir
from typing import Any, Optional

from .exceptions import AnastellosException, AnastellosInitError
from .utils import fetch_json

_log = logging.getLogger(__name__)


class SimpleConfig:
    def __init__(self, filename: str, **kwargs):
        self._def_schema = {}
        for arg, value in kwargs.items():
            self.__setattr__(arg, value)
            self._def_schema[arg] = value
        self._schema = self._def_schema
        self._filename = filename

    def __assignattrs__(self) -> None:
        try:
            cfg = self.get_config(filename=self._filename, schema=self._schema)
        except json.JSONDecodeError:
            cfg = self._schema
            _log.warn('Using the default config.')
        for key in self._def_schema.keys():
            try:
                self.__setattr__(key, cfg[key])
            except KeyError as e:
                _log.fatal(f'Global configuration entry "{key}" wasn\'t found.', exc_info=True)
                raise AnastellosInitError(__stage__='config') from e
        return None

    def __compileschema__(self) -> None:
        self._schema = {key: self.__getattribute__(
            key) for key in self._def_schema.keys()}
        return None

    def __resetschema__(self) -> None:
        self._schema = self._def_schema
        return None

    def save(self) -> None:
        self.__compileschema__()
        with open(f'{self._filename}.json', 'w', encoding="utf-8") as f:
            json.dump(self._schema, f, indent=4, ensure_ascii=False)
        self.__assignattrs__()
        return None

    @staticmethod
    def get_config(filename: str = 'cfg', schema: dict = {}) -> dict:
        """Fetch or create a config file.

        Args:
            filename: JSON file name without extension.
            schema: Default file content.

        Returns:
            Config in the form of dictionary.

        Raises:
            FileNotFoundError: If file is not found and no schema was defined.
            JSONDecodeError: If the file is not valid JSON and the schema is not defined.
        """
        try:
            return fetch_json(filename)
        except FileNotFoundError as e:
            if schema is not None:
                _log.warn(f'Creating a new file at {filename}.json and using the default config.')
                with open(f'{filename}.json', mode='x', encoding='utf8') as f:
                    json.dump(schema, f, indent=4, ensure_ascii=False)
                    return schema
            raise e
        except json.JSONDecodeError as e:
            if schema is not None:
                _log.warn(f'Overwriting the file at {filename}.json and using the default config.')
                with open(f'{filename}.json', mode='x', encoding='utf8') as f:
                    json.dump(schema, f, indent=4, ensure_ascii=False)
                    return schema
            raise e


class Config(SimpleConfig):
    def __init__(self, filename: str = 'cfg', *, additional_guild_params: dict[str, tuple[str, Any]] = {}, additional_global_params: dict[str] = {}, **kwargs):
        super().__init__(filename, **kwargs)

        # Settings that go into cfg.json.
        self.__settings = ['name', 'stage', 'mode', 'version',
                           'def_prefix', 'owner', 'demand_agreement']
        for k, default in additional_global_params.items():
            self.__settings.append(k)
            self.__setattr__(k, default)

        self.name: str = 'Anastellos Engine'
        self.stage: str = 'Release'
        self.mode: int = 0
        self.version: str = '1.0'
        self.def_prefix: str = 'ae!'
        self.owner = None
        self.demand_agreement: bool = False

        self._def_schema = {name: self.__getattribute__(
            name) for name in self.__settings}
        self._schema = self._def_schema

        self.__assignattrs__()
        self.__compileschema__()

        # Settings that stay in the memory.
        self.self_avatar_url = ''
        self._langfiles_path = 'jsons/langs/'
        self._def_guild_config = {  # Revision 2
            "is_eula_accepted": False,
            "prefix": self.def_prefix,
            "lang": "en"
        }
        self.build = '1.0.0.1'
        self.additional_guild_params = additional_guild_params
        for name, value in self.additional_guild_params.items():
            self._def_guild_config[name] = value[1]

        langfiles = listdir(self._langfiles_path)
        self.lang_names = set()  # Set of loaded language codes.
        for langn in langfiles:
            if langn.startswith(('ign_', '__')):
                continue
            self.lang_names.add(langn[:-5] if langn.endswith('.json') else langn)
        if not self.lang_names:
            _log.fatal('No localization files found. The bot is unable to initialize.')
            raise AnastellosInitError(__stage__='config')

        for arg, value in kwargs.items():
            self.__setattr__(arg, value)

    @property
    def full_version(self) -> str:
        return f'{self.stage+" " if self.stage.lower() != "release" else ""}{self.version} [AE {self.build}]'


class GuildConfigFile(SimpleConfig):
    def __init__(self, bot, filename='server_cfg', *, additional_guild_params={}):
        super().__init__(filename)

        self.__currev__ = 2  # Revision 2

        self.__settings = ('__revision__', 'guilds')

        self.__revision__ = self.__currev__
        self.guilds = {}

        self._def_schema = {name: self.__getattribute__(
            name) for name in self.__settings}
        self._schema = self._def_schema

        self.bot = bot
        self.additional_guild_params = additional_guild_params

        self._file = SimpleConfig.get_config(filename, self._def_schema)
        self.__revision__ = self._file.get('__revision__', 0)
        if self.__revision__ < self.__currev__:
            self.__upgrade(self.__revision__, self.__currev__)
        self.__assignattrs__()
        self.__compileschema__()

    def get_guild_cfg(self, guild_id):
        try:
            return GuildConfigEntry(self, guild_id, additional_guild_params=self.additional_guild_params)
        except KeyError:
            return None
        # return self.guilds.get(guild_id, None)

    def create_guild_cfg(self, guild_id):
        return GuildConfigEntry(self, guild_id, additional_guild_params=self.additional_guild_params, try_create=True)

    def _save_guild_cfg(self, guild_id: int, data: dict) -> None:
        self.guilds[str(guild_id)].update(data)
        self.save()
        return None

    def delete_guild_entry(self, guild_id: int) -> bool:
        entry = self.guilds.pop(str(guild_id), False)
        self.save()
        return bool(entry)

    def __upgrade(self, old_rev: int, new_rev: Optional[int] = None) -> None:
        def to1():
            self._file = {
                '__revision__': 1,
                'guilds': self._file
            }

        def to2():
            for guildid in self._file['guilds'].keys():
                self._file['guilds'][guildid] = {
                    'is_eula_accepted': False
                } | self._file['guilds'][guildid]
            self._file['__revision__'] = 2

        if new_rev is not None and new_rev < old_rev:
            raise AnastellosException('Can\t downgrade a config file.')

        while new_rev is None or old_rev < new_rev:
            if old_rev == 0:
                to1()
                _log.info('The guild config file was upgraded to revision 1 successfully.')
            elif old_rev == 1:
                to2()
                _log.info('The guild config file was upgraded to revision 2 successfully.')
            else:
                break
            old_rev += 1
        self._schema = self._file.copy()
        self.save()
        return None


class GuildConfigEntry(SimpleConfig):
    def __init__(self, guildConfigFile: GuildConfigFile, guild_id: int, *, try_create: bool = False, additional_guild_params: dict = {}):
        super().__init__('_')
        del self._filename

        self.try_create = try_create
        self._def_schema = {  # Revision 2
            "prefix": guildConfigFile.bot.config.def_prefix,
            "lang": "en",
            "is_eula_accepted": False
        }
        self.additional_guild_params = additional_guild_params
        for name, value in self.additional_guild_params.items():
            self._def_schema[name] = value[1]

        self._schema = self._def_schema
        self._guildConfigFile = guildConfigFile
        self._guild_id = guild_id
        self.__assignattrs__()
        self.__compileschema__()

    def __assignattrs__(self) -> None:
        if self.try_create:
            cfg = self._guildConfigFile._schema['guilds']
            try:
                cfg = cfg[str(self._guild_id)]
            except KeyError:
                self._guildConfigFile._schema['guilds'][str(
                    self._guild_id)] = self._def_schema.copy()
                cfg = self._guildConfigFile._schema['guilds'][str(
                    self._guild_id)]
        else:
            cfg = self._guildConfigFile._schema['guilds'][str(self._guild_id)]
        for key in self._def_schema.keys():
            self.__setattr__(key, cfg.get(
                key, self.additional_guild_params.get(key, (None, None))[1]))
        return None

    def __int__(self) -> int:
        return self._guild_id

    def save(self) -> None:
        self.__compileschema__()
        self._guildConfigFile._save_guild_cfg(self._guild_id, self._schema)
        self.__assignattrs__()
        return None

    def delete(self) -> None:
        self._guildConfigFile.delete_guild_entry(self._guild_id)
        return None

    @property
    def id(self) -> int:
        return self._guild_id

    @property
    def get_dict(self) -> dict[str]:
        self.__compileschema__()
        return self._schema
