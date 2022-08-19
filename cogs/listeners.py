import nextcord
from nextcord.ext import commands

from ..checks import reply_or_send
from ..classes import AnastellosCog
from ..utils import fetch_json, localization, write_config


class Listeners(AnastellosCog):
    @commands.Cog.listener(name='on_reaction_add')
    async def del_message(self, reaction: nextcord.Reaction, user: nextcord.Member):
        if reaction.message.author != self.bot.user:
            return
        if reaction.emoji == '❌':
            return await reaction.message.delete()
        if reaction.message.channel.permissions_for(reaction.message.guild.me).read_message_history:
            return await reaction.message.clear_reaction('❌')
        return None

    @commands.Cog.listener(name='on_guild_join')
    async def new_server_cfg(self, guild: nextcord.Guild):
        print(
            f'[INFO] Joined a server. Name: {guild.name}, ID: {guild.id}. Checking for a config... ', end='')
        if fetch_json('server_cfg').get(str(guild.id), False):
            print('Already existing.')
            return None
        new_cfg = self.bot.config._def_guild_config
        pref_locale = guild.preferred_locale
        if pref_locale and pref_locale in self.bot.config.lang_names:
            new_cfg['lang'] = guild.preferred_locale[:2]
        write_config(new_cfg, guild.id, filename='server_cfg')
        print('None existing, new one generated.')
        return None

    @commands.Cog.listener(name='on_guild_remove')
    async def on_guild_leave(self, guild: nextcord.Guild):
        print(f'[INFO] Left a guild. Name: {guild.name}, ID: {guild.id}.')
        return None

    @commands.Cog.listener(name='on_ready')
    async def new_server_check_cfg(self):
        new_cfg = self.bot.config._def_guild_config
        try:
            cfg = fetch_json('server_cfg')
        except FileNotFoundError:
            write_config(new_cfg, 0, filename='server_cfg')
            return None
        for guild in self.bot.guilds:
            new_cfg = self.bot.config._def_guild_config
            if str(guild.id) not in cfg:
                pref_locale = guild.preferred_locale
                if pref_locale and pref_locale in self.bot.config.lang_names:
                    new_cfg['lang'] = guild.preferred_locale[:2]
                write_config(new_cfg, guild.id, filename='server_cfg')
                return None
        return None

    @commands.Cog.listener('on_command_error')
    async def error_handler(self, ctx: commands.Context, error):
        await reply_or_send(ctx)
        delete_after = 10
        l10n = localization(guild_id=ctx.guild.id)[
            'anastellos']['global_errors']
        if isinstance(error, commands.MissingPermissions):
            await ctx.reply(l10n['insufficient_perms'], delete_after=delete_after)
        elif isinstance(error, commands.BotMissingPermissions):
            await ctx.reply(l10n['bot_insufficient_perms'], delete_after=delete_after)
        elif isinstance(error, commands.ChannelNotFound):
            await ctx.reply(l10n['channel_not_found'], delete_after=delete_after)
            print(f'[WARN] {ctx.author} entered a non-existing channel {error.argument} while trying to use {ctx.command.name} @ #{ctx.channel.name} ({ctx.guild.name}).')
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.reply(l10n['missing_required_argument'], delete_after=delete_after)
            print(f'[WARN] {ctx.author} missed the argument "{error.param.name}" while trying to use {ctx.command.name} @ #{ctx.channel.name} ({ctx.guild.name}).')
        elif isinstance(error, commands.BadArgument):
            await ctx.reply(l10n['bad_argument'], delete_after=delete_after)
            print(
                f'[WARN] {ctx.author} entered the invalid arguments while trying to use {ctx.command.name} @ #{ctx.channel.name} ({ctx.guild}).')
        elif isinstance(error, commands.MaxConcurrencyReached):
            await ctx.reply(l10n['max_concurrency'], delete_after=delete_after)
            print(
                f'[WARN] {ctx.author} entered the invalid arguments while trying to use {ctx.command.name} @ #{ctx.channel.name} ({ctx.guild.name}).')
        elif isinstance(error, commands.NotOwner):
            await ctx.reply(l10n['not_owner'], delete_after=5)
        elif isinstance(error, commands.CommandNotFound):
            await ctx.reply(l10n['command_not_found'], delete_after=delete_after)
        elif isinstance(error, commands.CommandInvokeError) and isinstance(error.original, nextcord.Forbidden):
            if error.original.code == 160002:
                await ctx.send(l10n.get('no_history_access', f'`{error.original.text}`'), delete_after=delete_after)
                return
            await ctx.reply(l10n['forbidden'], delete_after=delete_after)
            print(
                f'[WARN] {ctx.author} provoked an access violation while trying to use {ctx.command.name} @ #{ctx.channel.name} ({ctx.guild.name}).')
        else:
            raise error


def setup(bot):
    bot.add_cog(Listeners(bot))
