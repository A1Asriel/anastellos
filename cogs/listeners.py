import logging
from traceback import format_exception

import nextcord
from nextcord.ext import commands

from ..checks import reply_or_send
from ..classes import AnastellosInternalCog
from ..config import GuildConfigEntry
from ..exceptions import L10nUnsupported
from ..utils import localization

_log = logging.getLogger(__name__)


class Listeners(AnastellosInternalCog):
    @commands.Cog.listener(name='on_guild_join')
    async def new_server_cfg(self, guild: nextcord.Guild):
        _log.info(
            f'Joined a server. Name: {guild.name}, ID: {guild.id}. Checking for a config... ')
        if self.bot.guild_config.get_guild_cfg(guild.id) is not None:
            _log.info('Already existing.')
            return None
        if not self.bot.config.demand_agreement:
            _log.info('None existing, creating a new one.')
            entry: GuildConfigEntry = self.bot.guild_config.create_guild_cfg(guild.id)
            pref_locale = guild.preferred_locale
            if pref_locale and pref_locale in self.bot.l10n.lang_list:
                entry.lang = guild.preferred_locale[:2]
                entry.save()
            return None
        _log.info('None existing, waiting for an admin to accept the agreement.')
        return None

    @commands.Cog.listener(name='on_guild_remove')
    async def on_guild_leave(self, guild: nextcord.Guild):
        _log.info(f'Left a guild. Name: {guild.name}, ID: {guild.id}.')
        return None

    @commands.Cog.listener(name='on_ready')
    async def new_server_check_cfg(self):
        if self.bot.config.demand_agreement:
            return None
        for guild in self.bot.guilds:
            entry = self.bot.guild_config.get_guild_cfg(guild.id)
            if entry is None:
                entry = self.bot.guild_config.create_guild_cfg(guild.id)
                pref_locale = guild.preferred_locale
                if pref_locale and pref_locale in self.bot.l10n.lang_list:
                    entry.lang = guild.preferred_locale[:2]
                    entry.save()
        return None

    @commands.Cog.listener('on_command_error')
    async def error_handler(self, ctx: commands.Context, exception: commands.CommandError):
        is_debug = self.bot.config.mode == 2
        exc_text = '\n```py\n' + ''.join(format_exception(None, exception, exception.__traceback__)) + '\n```'
        l10n_code = ''
        console_msg = ''
        await reply_or_send(ctx)
        delete_after = 10

        if isinstance(exception, commands.MissingPermissions):
            l10n_code = 'insufficient_perms'
        elif isinstance(exception, commands.BotMissingPermissions):
            l10n_code = 'bot_insufficient_perms'
        elif isinstance(exception, commands.ChannelNotFound):
            l10n_code = 'channel_not_found'
            console_msg = f'{ctx.author} entered a non-existing channel {exception.argument} while trying to use {ctx.command.name} @ #{ctx.channel.name} ({ctx.guild.name}).'
        elif isinstance(exception, commands.MissingRequiredArgument):
            l10n_code = 'missing_required_argument'
            console_msg = f'{ctx.author} missed the argument "{exception.param.name}" while trying to use {ctx.command.name} @ #{ctx.channel.name} ({ctx.guild.name}).'
        elif isinstance(exception, (commands.BadArgument, commands.BadUnionArgument)):
            l10n_code = 'bad_argument'
            console_msg = f'{ctx.author} entered the invalid arguments while trying to use {ctx.command.name} @ #{ctx.channel.name} ({ctx.guild}).'
        elif isinstance(exception, commands.MaxConcurrencyReached):
            l10n_code = 'max_concurrency'
            console_msg = f'{ctx.author} tried to use {ctx.command.name} more times in a row than allowed @ #{ctx.channel.name} ({ctx.guild.name}).'
        elif isinstance(exception, commands.NotOwner):
            l10n_code = 'not_owner'
        elif isinstance(exception, commands.CommandNotFound):
            l10n_code = 'command_not_found'
        elif isinstance(exception, L10nUnsupported):
            l10n_code = 'l10n_unsupported'
        elif isinstance(exception, commands.CommandInvokeError) and isinstance(exception.original, nextcord.Forbidden):
            if exception.original.code == 160002:
                # Typically, this is avoided by using `reply_or_send` fix.
                l10n_code = 'no_history_access'
            else:
                l10n_code = 'forbidden'
                console_msg = f'{ctx.author} provoked an access violation while trying to use {ctx.command.name} @ #{ctx.channel.name} ({ctx.guild.name}).'
        elif (
            isinstance(exception, commands.CheckFailure) and
            (self.bot.guild_config.get_guild_cfg(ctx.guild.id) is None or
             not self.bot.guild_config.get_guild_cfg(ctx.guild.id).is_eula_accepted)
        ):
            pass
        else:
            console_msg = 'Internal error'
            if is_debug:
                l10n_code = 'internal_error'

        if self.bot.guild_config.get_guild_cfg(ctx.guild.id) is None or not self.bot.guild_config.get_guild_cfg(ctx.guild.id).is_eula_accepted and self.bot.config.demand_agreement:
            l10n_code = ''
            console_msg = ''

        if console_msg:
            _log.error(console_msg, exc_info=exception if is_debug else None)

        if l10n_code:
            l10n = localization(self.bot, guild_id=ctx.guild.id)[
                'anastellos']['errors']
            try:
                await ctx.reply(f'{l10n.get(l10n_code, "`"+l10n_code+"`")}{exc_text if is_debug else ""}', delete_after=delete_after if not is_debug else None)
            except nextcord.Forbidden:
                _log.error(
                    f'Couldn\'t send an error message to {ctx.channel.name}.')


def setup(bot):
    bot.add_cog(Listeners(bot))
