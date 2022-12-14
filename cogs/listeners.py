import nextcord
from nextcord.ext import commands

from ..checks import reply_or_send
from ..classes import AnastellosInternalCog
from ..config import GuildConfigEntry
from ..utils import localization


class Listeners(AnastellosInternalCog):
    @commands.Cog.listener(name='on_guild_join')
    async def new_server_cfg(self, guild: nextcord.Guild):
        print(
            f'[INFO] Joined a server. Name: {guild.name}, ID: {guild.id}. Checking for a config... ', end='')
        if self.bot.guild_config.get_guild_cfg(guild.id) is not None:
            print('Already existing.')
            return None
        if not self.bot.config.demand_agreement:
            print('None existing, creating a new one.')
            entry: GuildConfigEntry = self.bot.guild_config.create_guild_cfg(self.bot.guild_config, guild.id)
            pref_locale = guild.preferred_locale
            if pref_locale and pref_locale in self.bot.config.lang_names:
                entry.lang = guild.preferred_locale[:2]
                entry.save()
            return None
        new_cfg = self.bot.config._def_guild_config
        if pref_locale and pref_locale in self.bot.config.lang_names:
            new_cfg['lang'] = guild.preferred_locale[:2]
        print('None existing, waiting for a user to accept the agreement.')
        return None

    @commands.Cog.listener(name='on_guild_remove')
    async def on_guild_leave(self, guild: nextcord.Guild):
        print(f'[INFO] Left a guild. Name: {guild.name}, ID: {guild.id}.')
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
                if pref_locale and pref_locale in self.bot.config.lang_names:
                    entry.lang = guild.preferred_locale[:2]
                    entry.save()
        return None

    @commands.Cog.listener('on_command_error')
    async def error_handler(self, ctx: commands.Context, error):
        l10n_code = ''
        console_msg = ''
        await reply_or_send(ctx)
        delete_after = 10

        if isinstance(error, commands.MissingPermissions):
            l10n_code = 'insufficient_perms'
        elif isinstance(error, commands.BotMissingPermissions):
            l10n_code = 'bot_insufficient_perms'
        elif isinstance(error, commands.ChannelNotFound):
            l10n_code = 'channel_not_found'
            console_msg = f'[WARN] {ctx.author} entered a non-existing channel {error.argument} while trying to use {ctx.command.name} @ #{ctx.channel.name} ({ctx.guild.name}).'
        elif isinstance(error, commands.MissingRequiredArgument):
            l10n_code = 'missing_required_argument'
            console_msg = f'[WARN] {ctx.author} missed the argument "{error.param.name}" while trying to use {ctx.command.name} @ #{ctx.channel.name} ({ctx.guild.name}).'
        elif isinstance(error, commands.BadArgument):
            l10n_code = 'bad_argument'
            console_msg = f'[WARN] {ctx.author} entered the invalid arguments while trying to use {ctx.command.name} @ #{ctx.channel.name} ({ctx.guild}).'
        elif isinstance(error, commands.MaxConcurrencyReached):
            l10n_code = 'max_concurrency'
            console_msg = f'[WARN] {ctx.author} entered the invalid arguments while trying to use {ctx.command.name} @ #{ctx.channel.name} ({ctx.guild.name}).'
        elif isinstance(error, commands.NotOwner):
            l10n_code = 'not_owner'
        elif isinstance(error, commands.CommandNotFound):
            l10n_code = 'command_not_found'
        elif isinstance(error, commands.CommandInvokeError) and isinstance(error.original, nextcord.Forbidden):
            if error.original.code == 160002:
                # Typically, this is avoided by using `reply_or_send` fix.
                l10n_code = 'no_history_access'
            else:
                l10n_code = 'forbidden'
                console_msg = f'[WARN] {ctx.author} provoked an access violation while trying to use {ctx.command.name} @ #{ctx.channel.name} ({ctx.guild.name}).'
        elif isinstance(error, commands.CheckFailure) and (ctx.bot.guild_config.get_guild_cfg(ctx.guild.id) is None or not ctx.bot.guild_config.get_guild_cfg(ctx.guild.id).is_eula_accepted):
            pass
        else:
            raise error

        if self.bot.guild_config.get_guild_cfg(ctx.guild.id) is None or not ctx.bot.guild_config.get_guild_cfg(ctx.guild.id).is_eula_accepted:
            l10n_code = ''
            console_msg = ''

        if l10n_code:
            l10n = localization(self.bot, guild_id=ctx.guild.id)[
                'anastellos']['global_errors']
            await ctx.reply(l10n[l10n_code], delete_after=delete_after)

        if console_msg:
            print(console_msg)


def setup(bot):
    bot.add_cog(Listeners(bot))
