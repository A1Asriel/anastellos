__build__ = '2.1.23143.2'

from logging import getLogger
from os import listdir
from time import time

import nextcord
from nextcord.ext.commands.errors import ExtensionFailed

from .classes import AESnowflake, AnastellosBot
from .config import Config, GuildConfigFile
from .exceptions import AnastellosInitError
from .help import AEHelpCommand
from .l10n import Localization
from .utils import get_commit_details, get_prefix

_log = getLogger(__name__)


class AnastellosEngine:
    def __init__(self, *, additional_guild_params={}, additional_global_params={}):
        self.config = Config(
            additional_guild_params=additional_guild_params, additional_global_params=additional_global_params, build=__build__)

        if self.config.mode == 2:
            getLogger().setLevel(10)
            getLogger('nextcord').setLevel(20)
        else:
            getLogger('nextcord').propagate = False

        _log.info(f'Starting {self.config.name} {self.config.full_version}...')

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
        self.bot.l10n = Localization()
        if self.config.mode == 2:
            try:
                bot_repo_prefix = '.git/'
                bot_commit_details = get_commit_details(bot_repo_prefix)
                self.config.version += f' {bot_commit_details[0]}:{bot_commit_details[1][:7]}'
            except Exception as e:
                _log.debug(f'Couldn\'t retrieve bot repository info while starting up.', exc_info=1)
            _log.warn('The bot is running in DEBUG mode. Please do not use it on a common basis. Turn it off as soon as possible if you are not testing anything!')

        @self.bot.event
        async def on_ready():
            self.bot.startup_time = time()
            _log.info(f'Logged in as {str(self.bot.user)} - {self.bot.user.id}.')
            _log.info(f'The bot is running on {len(self.bot.guilds)} guilds.')
            guildlist = '\n'.join([f'{guild.id} - {guild.name}' for guild in self.bot.guilds])
            _log.debug(f'Current guilds:\n{guildlist}')
            
            if self.bot.user.avatar is not None:
                self.config.self_avatar_url = self.bot.user.avatar.url
            self.bot.owner_id = self.config.owner if self.config.owner is not None else (await self.bot.application_info()).owner.id

    def load_cog(self, path: str, *, type: str = ''):
        try:
            files = listdir(path)
        except FileNotFoundError as e:
            _log.error(f'Failed to find directory named {path}. Skipping it.')
            return None
        for cog in files:
            path = path.replace('/', '.')
            if cog.endswith('.py') and cog[-7:-3] != '_dis' and not cog.startswith('__'):
                _log.info(f'Initializing {type}cog {cog}...')
                try:
                    self.bot.load_extension(f'{path}.{cog[:-3]}')
                except ExtensionFailed as exception:
                    _log.error(f'Failed to initialize extension {cog}!')
                    inp = input('Skip it? Y/n: ').lower()
                    if 'no'.startswith(inp):
                        incl_trace = self.bot.config.mode == 2
                        _log.fatal('Bot initializing halted.', exc_info=incl_trace)
                        exit(1)

    def load_cogs(self):
        self.load_cog('anastellos/cogs', type='internal ')
        self.load_cog('cogs')
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
