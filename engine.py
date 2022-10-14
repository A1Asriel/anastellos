__build__ = '2.1.22281.2'

import logging
import time

import nextcord

from .classes import AESnowflake, AnastellosBot
from .config import Config, GuildConfigFile
from .exceptions import *
from .help import AEHelpCommand
from .utils import *

_log = logging.getLogger(__name__)


class AnastellosEngine:
    def __init__(self, *, additional_guild_params={}, additional_global_params={}):
        self.config = Config(
            additional_guild_params=additional_guild_params, additional_global_params=additional_global_params, build=__build__)

        if self.config.mode == 2:
            logging.getLogger().setLevel(10)
            logging.getLogger('nextcord').setLevel(20)
        else:
            logging.getLogger('nextcord').propagate = False

        _log.info(f'Starting {self.config.name} {self.config.full_version}')

        if self.config.mode == 2:
            activity = nextcord.Game(
                f'DEBUG mode. The bot may operate unstable. | {self.config.full_version}')
            status = nextcord.Status.dnd
        elif self.config.mode == 1:
            activity = nextcord.Game(
                f'{self.config.full_version} | Some bugs may occur.')
            status = nextcord.Status.idle
        else:
            activity = nextcord.Game(f'{self.config.full_version}')
            status = nextcord.Status.online

        intents = nextcord.Intents.all()
        allowed_mentions = nextcord.AllowedMentions.all()
        allowed_mentions.replied_user = False
        help_command = AEHelpCommand()

        self.bot = AnastellosBot(config=self.config,
                                 command_prefix=get_prefix,
                                 intents=intents,
                                 activity=activity,
                                 status=status,
                                 allowed_mentions=allowed_mentions,
                                 help_command=help_command
                                 )

        self.guild_config = GuildConfigFile(
            self.bot, additional_guild_params=additional_guild_params)
        self.bot.guild_config = self.guild_config
        self.bot.aesnowflake = AESnowflake(self.bot.shard_id)

        @self.bot.event
        async def on_ready():
            self.bot.startup_time = time.time()
            guildlist = ', '.join(
                ['"' + j.name + '"' for j in self.bot.guilds])
            _log.info(
                f'Logged in as {self.bot.user.name}#{self.bot.user.discriminator} ({self.bot.user.id}).\nBot is running on servers: {guildlist}.')
            if self.config.mode == 2:
                _log.warn('The bot is running in DEBUG mode. Please do not use it on a common basis. Turn it off as soon as possible if you are not testing anything!')
            if self.bot.user.avatar is not None:
                self.config.self_avatar_url = self.bot.user.avatar.url
            self.bot.owner_id = self.config.owner if self.config.owner is not None else (await self.bot.application_info()).owner.id

    def load_cogs(self):
        loadcog(self.bot, 'anastellos/cogs', 'internal ')
        loadcog(self.bot, 'cogs')
        if not self.bot.get_cog('Settings'):
            _log.warn('No custom settings cog found, falling back to the default one.')
            from .classes import Settings
            self.bot.add_cog(Settings(self.bot))

    def start(self):
        try:
            with open('token.txt') as f:
                TOKEN = f.read()
        except FileNotFoundError as e:
            _log.fatal('Cannot access the token file. The bot is unable to start.')
            raise AnastellosInitError(__stage__='token') from e
        self.bot.run(TOKEN, reconnect=True)
