import json
import os
from json.decoder import JSONDecodeError

from nextcord import Message
from nextcord.ext.commands import Bot
from nextcord.ext.commands.errors import ExtensionFailed

# from anastellos.classes import AnastellosBot  Won't fix: cannot import.


def fetch_json(filename: str) -> dict:
    """Fetch JSON file.

    Args:
        filename: JSON file name without extension.

    Returns:
        Dictionary.

    Raises:
        FileNotFoundError: If there is no file with the specified name.
        JSONDecodeError: If the file is not valid JSON.
    """
    try:
        with open(f'{filename}.json', encoding='utf8') as data:
            return json.load(data)
    except FileNotFoundError as exception:
        print(f'[ERROR] JSON file at {filename}.json wasn\'t found.')
        raise exception
    except JSONDecodeError as exception:
        print(f'[ERROR] JSON file at {filename} couldn\'t be read.')
        if exception.args[0] == 'Expecting value: line 1 column 1 (char 0)':
            print('[ERROR] Maybe the entry brackets are missing?')
        raise exception


def write_config(append: dict, guildid: int | str, filename: str = 'server_cfg'):
    """Modify the specified servers config file.

    Args:
        append: New data that needs to be inserted into the config file. Overwrites the existing data.
        guildid: The ID of the guild whose config needs to be modified.
        filename: JSON file name without extension.

    Raises:
        JSONDecodeError: If the file is not valid JSON.
    """
    mode = 'w'
    try:
        cfg = fetch_json(filename)
    except JSONDecodeError as exception:
        print('[ERROR] JSON file is corrupted, cannot modify it.')
        raise exception

    if isinstance(guildid, int):
        guildid = str(guildid)
    try:
        cfg['guilds'][guildid].update(append)
    except KeyError:
        cfg['guilds'][guildid] = {}
        cfg['guilds'][guildid].update(append)
    try:
        with open(f'{filename}.json', encoding='utf8', mode=mode) as out:
            json.dump(cfg, out, indent=4)
    except:
        print('[WARN] JSON file can\'t be written.')


def delete_guild_config(guild_id: int | str, filename: str):
    if isinstance(guild_id, int):
        guild_id = str(guild_id)
    cfg = fetch_json(filename)['guilds']
    cfg.pop(guild_id)
    with open(f'{filename}.json', encoding='utf8', mode='w') as out:
        json.dump(cfg, out, indent=4)


def loadcog(bot: Bot, path: str, type: str = ''):
    for cog in os.listdir(path):
        path = path.replace('/', '.')
        if cog.endswith('.py') and cog[-7:-3] != '_dis' and not cog.startswith('__'):
            print(f'[INFO] Initializing {type}cog {cog}...')
            try:
                bot.load_extension(f'{path}.{cog[:-3]}')
            except ExtensionFailed as exception:
                print(f'[ERROR] Failed to initialize extension {cog}!')
                inp = input('Skip it? YES/No/Raise: ').lower()
                if inp == 'n' or inp == 'no':
                    input('[FATAL] Bot initializing halted.\nPress Enter to close.')
                    exit()
                elif inp == 'r' or inp == 'raise':
                    raise exception


def get_prefix(bot: Bot, msg: Message):
    prefixes = [f'{bot.user.mention} ']
    try:
        prefixes.append(bot.guild_config.get_guild_cfg(msg.guild.id).prefix)
    except:
        prefixes.append(bot.config.def_prefix)
    return prefixes


def localization(bot: Bot, guild_id: int | str = None, lang: str = None) -> dict:
    if guild_id is not None:
        if isinstance(guild_id, int):
            guild_id = str(guild_id)
        lang = bot.guild_config.get_guild_cfg(guild_id).lang
    return fetch_json('jsons/langs/'+lang)
