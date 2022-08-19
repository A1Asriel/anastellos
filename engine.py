__build__ = '2.0.22222.4'

import nextcord

from .classes import AnastellosBot
from .config import Config
from .exceptions import *
from .help import AEHelpCommand
from .utils import *


class AnastellosEngine:
    def __init__(self, *, additional_guild_params={}):
        self.config = Config(additional_guild_params=additional_guild_params, build=__build__)

        print(f'- {self.config.name} {self.config.full_version} -', end='')
        if self.config.mode == 'indev':
            print(' INDEV', end='')
        print('\n')

        if self.config.mode == 'indev':
            activity = nextcord.Game(
                f'INDEV mode. The bot may operate unstable. | {self.config.full_version}')
            status = nextcord.Status.dnd
        elif self.config.mode == 'preview':
            activity = nextcord.Game(
                f'{self.config.full_version} | Some bugs may occur.')
            status = nextcord.Status.idle
        else:
            activity = nextcord.Game(f'{self.config.full_version}')
            status = nextcord.Status.online

        intents = nextcord.Intents.all()
        allowed_mentions = nextcord.AllowedMentions.all()
        allowed_mentions.replied_user = False

        self.bot = AnastellosBot(config=self.config,
                                 command_prefix=get_prefix,
                                 intents=intents,
                                 activity=activity,
                                 status=status,
                                 allowed_mentions=allowed_mentions,
                                 help_command=AEHelpCommand()
                                 )
        self.bot.owner_id = self.config.owner

        @self.bot.event
        async def on_ready():
            print()
            guildlist = ', '.join(
                ['"' + j.name + '"' for j in self.bot.guilds])
            print(
                f'[INFO] Logged in as {self.bot.user.name}#{self.bot.user.discriminator} ({self.bot.user.id}).\nBot is running on servers: {guildlist}.')
            if self.config.mode == 'indev':
                print('[WARN] The bot is running in INDEV mode. Please do not use it on a common basis. Turn it off as soon as possible if you are not testing anything!')
            print('_______\n')
            if self.bot.user.avatar is not None:
                self.config.self_avatar_url = self.bot.user.avatar.url

    def load_cogs(self):
        loadcog(self.bot, 'anastellos/cogs', 'internal ')
        loadcog(self.bot, 'cogs')

    def start(self):
        try:
            with open('token.txt') as f:
                TOKEN = f.read()
        except FileNotFoundError:
            print(
                '[FATAL] Cannot access the token file. The bot is unable to initialize.')
            raise AnastellosInitError(__stage__='token')
        self.bot.run(TOKEN, reconnect=True)
