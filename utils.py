import json
import logging
import os
from json.decoder import JSONDecodeError
from typing import Union

from nextcord import Message
from nextcord.ext.commands import Bot
from nextcord.ext.commands.errors import ExtensionFailed

# from anastellos.classes import AnastellosBot  Won't fix: cannot import.

_log = logging.getLogger(__name__)


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
        _log.error(f'JSON file at {filename}.json wasn\'t found.')
        raise exception
    except JSONDecodeError as exception:
        _log.error(f'JSON file at {filename} couldn\'t be read.')
        if exception.args[0] == 'Expecting value: line 1 column 1 (char 0)':
            _log.error('Maybe the entry brackets are missing?')
        raise exception


def get_prefix(bot: Bot, msg: Message):
    prefixes = [f'{bot.user.mention} ']
    try:
        prefixes.append(bot.guild_config.get_guild_cfg(msg.guild.id).prefix)
    except:
        prefixes.append(bot.config.def_prefix)
    return prefixes


def localization(bot: Bot, guild_id: Union[int, str] = None, lang: str = None) -> dict:
    if guild_id is not None:
        if isinstance(guild_id, int):
            guild_id = str(guild_id)
        lang = bot.guild_config.get_guild_cfg(guild_id).lang
    return fetch_json('jsons/langs/'+lang)


def get_commit_details(repo_prefix: str):
    with open(f'{repo_prefix}HEAD', 'r', encoding='utf8') as f:
        branch = f.readline().strip()
        branch = branch[16:] if branch.startswith('ref: refs/heads/') else branch
    with open(f'{repo_prefix}refs/heads/{branch}', 'r', encoding='ansi') as f:
        commit_sha = f.readline().strip()
    with open(f'{repo_prefix}logs/refs/heads/{branch}', 'r', encoding='utf8') as f:
        timestamp = 0
        for l in f.readlines():
            elems = l.split()
            if elems[1] != commit_sha:
                continue
            timestamp = int(elems[4])
            break
    return branch, commit_sha, timestamp
