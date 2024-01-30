from datetime import datetime
from time import time
from typing import Optional, Union

from nextcord import Colour, Embed
from nextcord.ext import commands
from nextcord.ext.commands import Bot, Cog

from .checks import is_cog_enabled, is_eula_accepted, reply_or_send
from .config import Config, GuildConfigFile
from .exceptions import AnastellosException
from .l10n import Localization
from .utils import localization


class AnastellosBot(Bot):
    def __init__(self, config, **kwargs):
        super().__init__(**kwargs)
        self.config: Config = config
        self.guild_config: GuildConfigFile
        self.aesnowflake: AESnowflake
        self.l10n: Localization
        self.startup_time: float


class AnastellosCog(Cog):
    def __init__(self, bot: AnastellosBot):
        self.bot = bot
        self.__type__ = None

    async def cog_before_invoke(self, ctx):
        await reply_or_send(ctx)

    async def cog_check(self, ctx: commands.Context) -> bool:
        return (await is_eula_accepted(ctx)) and is_cog_enabled(ctx)


class AnastellosInternalCog(AnastellosCog):
    def __init__(self, bot: AnastellosBot):
        super().__init__(bot)
        self.__type__ = 'internal'

    async def cog_check(self, ctx: commands.Context) -> bool:
        return await is_eula_accepted(ctx)


class _AEEmbedDefault:
    def __bool__(self):
        return True


AEEmbedDefault = _AEEmbedDefault()


class Settings(AnastellosInternalCog):
    def get_flags(self, lang: dict = None):
        if lang:
            return lang['__meta__']['yes'], lang['__meta__']['no']
        yes = ()
        no = ()
        for lang_name in self.bot.l10n.lang_list:
            lang = self.bot.l10n.getlang(lang_name)
            yes += tuple(lang['__meta__']['yes'])
            no += tuple(lang['__meta__']['no'])
        return yes, no

    @commands.group()
    @commands.has_guild_permissions(manage_guild=True)
    async def settings(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            l10n = localization(self.bot, guild_id=ctx.guild.id)['anastellos']['cogs']['settings']['commands']['list']
            cfg = self.bot.guild_config.get_guild_cfg(ctx.guild.id).get_dict
            fields = [
                [l10n['prefix'], '`'+cfg['prefix']+'`', True],
                [l10n['lang'], cfg['lang'], True],
                [l10n['toggle_cog'], l10n['list'], True]
            ]
            for name, value in self.bot.config.additional_guild_params.items():
                if value[0] == 'str':
                    second_field = cfg[name]
                elif value[0] == 'bool':
                    second_field = l10n['enabled'] if cfg[name] else l10n['disabled']
                elif value[0] == 'channel':
                    second_field = self.bot.get_channel(
                        cfg[name]).mention if cfg[name] != 0 else l10n['disabled']
                elif value[0] == 'dict':
                    second_field = l10n['multilevel']
                elif value[0] == 'list':
                    second_field = l10n['list']
                fields += [[l10n.get(name, name), second_field, True]]
            await ctx.reply(embed=AEEmbed(self.bot, title=l10n['title'], fields=fields))

    @settings.command(name='prefix', aliases=('set_prefix',))
    async def set_prefix(self, ctx: commands.Context, *, new_prefix: str = None):
        l10n = localization(self.bot, guild_id=ctx.guild.id['anastellos']['cogs']['settings']['commands']['prefix'])
        if new_prefix is None:
            new_prefix = self.bot.config.def_prefix
        cfg = self.bot.guild_config.get_guild_cfg(ctx.guild.id)
        cfg.prefix = new_prefix
        cfg.save()
        return await ctx.reply(embed=AEEmbed(self.bot, title=l10n['title'], desc=l10n['desc'].format(new_prefix=new_prefix), colour=Colour.brand_green()))

    @settings.command(name='language', aliases=('lang', 'set_language', 'set_lang'))
    async def set_lang(self, ctx: commands.Context, new_lang: str):
        langs = {}
        langfiles = self.bot.l10n.lang_list
        for lang in langfiles:
            lang_aliases = self.bot.l10n.l10n_dict[lang]['__meta__']['aliases']
            langs[lang] = lang_aliases

        found = False
        for lang_name, lang in langs.items():
            if new_lang in lang:
                found = True
                new_lang = lang_name
                break
        if not found:
            raise commands.BadArgument

        cfg = self.bot.guild_config.get_guild_cfg(ctx.guild.id)
        cfg.lang = new_lang
        cfg.save()
        l10n = localization(self.bot, guild_id=ctx.guild.id)['anastellos']['cogs']['settings']['commands']['language']
        return await ctx.reply(embed=AEEmbed(self.bot, title=l10n['title'], desc=l10n['desc'], colour=Colour.brand_green()))

    @settings.command(name='toggle_cog', aliases=('cog',))
    async def toggle_cog(self, ctx: commands.Context, cog_name: str, status: Optional[Union[bool, str]] = None):
        def valid_cog(cog: Union[AnastellosCog, str]) -> bool:
            if isinstance(cog, str):
                cog = self.context.bot.get_cog(cog)
            for cmd in cog.walk_commands():
                if cmd.enabled and not cmd.hidden:
                    return True
            return False
        cog = self.bot.get_cog(cog_name)
        l10n = localization(self.bot, guild_id=ctx.guild.id)['anastellos']['cogs']['settings']['commands']['toggle_cog']
        if not (cog and valid_cog(cog)):
            return await ctx.reply(embed=AEEmbed(self.bot, title=l10n['title'], desc=l10n['nocog_error'], colour=Colour.brand_red()))
        if isinstance(cog, AnastellosInternalCog):
            return await ctx.reply(embed=AEEmbed(self.bot, title=l10n['title'], desc=l10n['intcog_error'], colour=Colour.brand_red()))
        guild_config = self.bot.guild_config.get_guild_cfg(ctx.guild.id)
        if status is None:
            status = l10n['inactive'] if cog_name in guild_config.disabled_cogs else l10n['active']
            return await ctx.reply(embed=AEEmbed(self.bot, title=l10n['title'], desc=l10n['status_desc'].format(cog_name=cog_name, status=status), colour=Colour.blurple() if cog_name not in guild_config.disabled_cogs else None))

        if isinstance(status, str):
            flags = self.get_flags()
            if status.lower() in ('1', '+') + flags[0]:
                status = True
            elif status.lower() in ('0', '-') + flags[1]:
                status = False
            else:
                raise commands.BadArgument

        if status:
            if cog_name in guild_config.disabled_cogs:
                guild_config.disabled_cogs.remove(cog_name)
            guild_config.save()
            return await ctx.reply(embed=AEEmbed(self.bot, title=l10n['title'], desc=l10n['enable_desc'].format(cog_name=cog_name, status=status), colour=Colour.brand_green()))

        if cog_name not in guild_config.disabled_cogs:
            guild_config.disabled_cogs.append(cog_name)
        guild_config.save()
        return await ctx.reply(embed=AEEmbed(self.bot, title=l10n['title'], desc=l10n['disable_desc'].format(cog_name=cog_name, status=status), colour=Colour.brand_red()))


class AEEmbed(Embed):
    """A formatted Anastellos Engine embed.

    Args:
        bot: AnastellosBot instance.
        title: Embed title. Can be empty.
        url: URL string for a title link. Can be empty.
        desc: Embed description. Can be empty.
        colour: Embed colour Nextcord object. Defaults to `#5865F2` (Discord Blurple).
        author_name: Embed author. Defaults to the bot's name plus its version.
        author_url: URL string for an author link. Can be empty.
        author_icon: Embed author icon URL. Defaults to the bot's avatar.
        footer_title: Embed footer title. Can be empty.
        footer_icon: Embed footer icon URL. Can be empty.
        fields: List of lists in the format of `[title, description, inline (bool)]`.
        image_url: URL string for an image. Can be empty.
        thumbnail_url: URL string for a thumbnail. Can be empty.
        timestamp: datetime instance. Can be empty.
    """

    def __init__(
        self,
        bot: AnastellosBot,
        *,
        title: str = None,
        url: str = None,
        desc: str = None,
        colour: Union[Colour, int] = Colour.blurple(),
        author_name: str = AEEmbedDefault,
        author_url: str = None,
        author_icon: str = AEEmbedDefault,
        footer_title: str = None,
        footer_icon: str = None,
        fields: Optional[Union[list, tuple]] = None,
        image_url: str = None,
        thumbnail_url: str = None,
        timestamp: Optional[datetime] = None
    ):
        if isinstance(self.colour, int):
            self.colour = Colour(self.colour)

        super().__init__(
            colour=colour,
            title=title,
            url=url,
            description=desc,
            timestamp=timestamp
        )

        self.author_name = author_name
        self.author_url = author_url
        self.author_icon = author_icon
        if self.author_name is AEEmbedDefault:
            self.author_name = f'{bot.config.name} {bot.config.full_version}'
            if bot.config.mode == 2:
                self.author_name += ' | DEBUG'
        if self.author_icon is AEEmbedDefault:
            self.author_icon = bot.config.self_avatar_url
        if self.author_name is not None:
            self.set_author(name=self.author_name,
                            url=self.author_url, icon_url=self.author_icon)

        self.footer_title = footer_title
        self.footer_icon = footer_icon
        if self.footer_title is not None:
            self.set_footer(text=self.footer_title, icon_url=self.footer_icon)

        self.image_url = image_url
        self.set_image(self.image_url)

        self.thumbnail_url = thumbnail_url
        self.set_thumbnail(self.thumbnail_url)

        self.auto_fields = fields
        if isinstance(self.auto_fields, (list, tuple)):
            for i in self.auto_fields:
                if isinstance(i, tuple):
                    i = list(i)
                if i[1] in ('', None):
                    i[1] = 'None'
                if len(i) == 3:
                    self.add_field(name=i[0], value=i[1], inline=i[2])
                elif len(i) == 2:
                    self.add_field(name=i[0], value=i[1], inline=False)
        
    @classmethod
    def from_dict(cls, bot: AnastellosBot, data: dict):
        return cls(bot,
                   title=data.get('title'),
                   url=data.get('url'),
                   desc=data.get('desc'),
                   colour=data.get('colour', data.get('color', Colour.blurple())),
                   author_name=data.get('author_name', AEEmbedDefault),
                   author_url=data.get('author_url'),
                   author_icon=data.get('author_icon', AEEmbedDefault),
                   footer_title=data.get('footer_title'),
                   footer_icon=data.get('footer_icon'),
                   fields=data.get('fields'),
                   image_url=data.get('image_url'),
                   thumbnail_url=data.get('thumbnail_url'),
                   timestamp=data.get('timestamp'))


class AESnowflake:
    AE_EPOCH = 1664037145000

    def __init__(self, shard_id: int = 0):
        self.shard_id = shard_id if shard_id else 0
        self.last_timestamp = 0
        self.incr = 0

    def generate(self) -> int:
        milliseconds = round(time() * 1000) - self.AE_EPOCH
        if milliseconds < self.last_timestamp:
            raise AnastellosException
        if milliseconds > self.last_timestamp:
            self.last_timestamp = milliseconds
            self.incr = 0
        else:
            self.incr += 1
        snowflake = (milliseconds << 22) + (self.shard_id << 17) + self.incr
        return snowflake

    def __int__(self) -> int:
        return self.generate()

    def __str__(self) -> str:
        return str(self.generate())
