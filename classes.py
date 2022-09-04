from datetime import datetime
from os import listdir

from nextcord import Colour, Embed
from nextcord.ext import commands
from nextcord.ext.commands import Bot, Cog

from .checks import reply_or_send, is_eula_accepted
from .config import Config, GuildConfigFile
from .utils import fetch_json, localization


class AnastellosBot(Bot):
    def __init__(self, config, **kwargs):
        super().__init__(**kwargs)
        self.config: Config = config
        self.guild_config: GuildConfigFile


class AnastellosCog(Cog):
    def __init__(self, bot: AnastellosBot):
        self.bot = bot

    async def cog_before_invoke(self, ctx):
        await reply_or_send(ctx)

    def cog_check(self, ctx: commands.Context) -> bool:
        return is_eula_accepted(ctx)


class AnastellosInternalCog(AnastellosCog):
    def __init__(self, bot: AnastellosBot):
        super().__init__(bot)
        self.__type__ = 'internal'


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
        for lang_name in self.bot.config.lang_names:
            lang = fetch_json(self.bot.config._langfiles_path + lang_name)
            yes += tuple(lang['__meta__']['yes'])
            no += tuple(lang['__meta__']['no'])
        return yes, no

    @commands.group()
    @commands.has_guild_permissions(manage_guild=True)
    async def settings(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            l10n = localization(self.bot, guild_id=ctx.guild.id)[
                'anastellos']['settings']['list']
            cfg = self.bot.guild_config.get_guild_cfg(ctx.guild.id).get_dict
            fields = [
                [l10n['prefix'], '`'+cfg['prefix']+'`'],
                [l10n['lang'], cfg['lang']]
            ]
            for name, value in self.bot.config.additional_guild_params.items():
                if value[0] == 'str':
                    second_field = cfg[name]
                elif value[0] == 'bool':
                    second_field = l10n['enabled'] if cfg[name] else l10n['disabled']
                elif value[0] == 'channel':
                    second_field = self.bot.get_channel(
                        cfg[name]).mention if cfg[name] != 0 else l10n['disabled']
                fields += [[l10n[name], second_field]]
            await ctx.reply(embed=AEEmbed(self.bot, title=l10n['title'], fields=fields))

    @settings.command(name='prefix', aliases=('set_prefix',))
    async def set_prefix(self, ctx: commands.Context, *, new_prefix: str = None):
        l10n = localization(self.bot, guild_id=ctx.guild.id)[
            'anastellos']['settings']['prefix']
        if new_prefix == None:
            new_prefix = self.bot.config.def_prefix
        cfg = self.bot.guild_config.get_guild_cfg(ctx.guild.id)
        cfg.prefix = new_prefix
        cfg.save()
        return await ctx.reply(embed=AEEmbed(self.bot, title=l10n['title'], desc=l10n['desc'].format(new_prefix=new_prefix), colour=Colour.brand_green()))

    @settings.command(name='language', aliases=('lang', 'set_language', 'set_lang'))
    async def set_lang(self, ctx: commands.Context, new_lang: str):
        langs = {}
        langfiles_path = 'jsons/langs/'
        langfiles = listdir(langfiles_path)
        for lang in langfiles:
            if lang.startswith(('ign_', '__')):
                continue
            lang_name = lang.removesuffix('.json')
            lang_aliases = fetch_json(
                langfiles_path + lang_name)['__meta__']['aliases']
            langs[lang_name] = lang_aliases

        found = False
        for lang in langs:
            if new_lang in langs[lang]:
                found = True
                new_lang = lang
                break
        if not found:
            raise commands.BadArgument

        cfg = self.bot.guild_config.get_guild_cfg(ctx.guild.id)
        cfg.lang = new_lang
        cfg.save()
        l10n = localization(self.bot, guild_id=ctx.guild.id)[
            'anastellos']['settings']['lang']
        return await ctx.reply(embed=AEEmbed(self.bot, title=l10n['title'], desc=l10n['desc'], colour=Colour.brand_green()))


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
        title: str = Embed.Empty,
        url: str = Embed.Empty,
        desc: str = Embed.Empty,
        colour: Colour | int = Colour.blurple(),
        author_name: str = AEEmbedDefault,
        author_url: str = Embed.Empty,
        author_icon: str = AEEmbedDefault,
        footer_title: str = Embed.Empty,
        footer_icon: str = Embed.Empty,
        fields: list | tuple | None = None,
        image_url: str = Embed.Empty,
        thumbnail_url: str = Embed.Empty,
        timestamp: datetime | None = None
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
            if bot.config.mode == 'indev':
                self.author_name += ' | INDEV'
        if self.author_icon is AEEmbedDefault:
            self.author_icon = bot.config.self_avatar_url
        self.set_author(name=self.author_name,
                        url=self.author_url, icon_url=self.author_icon)

        self.footer_title = footer_title
        self.footer_icon = footer_icon
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
