import logging
import os
import platform
import sys
import time
from timeit import default_timer

import nextcord
import psutil
from nextcord.ext import commands

from ..classes import AEEmbed, AnastellosInternalCog
from ..utils import get_commit_details, localization

_log = logging.getLogger(__name__)


class Technical(AnastellosInternalCog, command_attrs={'hidden': True}):
    @commands.command(aliases=('destroy',))
    @commands.guild_only()
    @commands.is_owner()
    async def stop(self, ctx: commands.Context):
        l10n = localization(self.bot, guild_id=ctx.guild.id)[
            'anastellos']['technical']['stop']
        await ctx.reply(l10n)
        return await self.bot.close()

    # Unsafe to use, this command is deprecated and to be removed in the future.
    """ @commands.command(enabled=False)
    @commands.guild_only()
    @commands.is_owner()
    async def shutdown(self, ctx: commands.Context):
        l10n = localization(self.bot, guild_id=ctx.guild.id)['anastellos']['technical']['shutdown']
        if self.bot.config.mode == 2:
            return await ctx.reply(l10n['error_indev'], delete_after=5)
        # if not self.bot.config.can_shutdown:
        #     return await ctx.reply(l10n['cant_shutdown'], delete_after=5)
        await ctx.reply(l10n['msg'])
        os.system('shutdown -s -t 10')
        return await self.bot.close() """

    @commands.command()
    @commands.guild_only()
    @commands.is_owner()
    async def reload(self, ctx: commands.Context):
        l10n = localization(self.bot, guild_id=ctx.guild.id)[
            'anastellos']['technical']['reload']
        msg = await ctx.reply(l10n['start'], delete_after=5)
        i = '$modulename'
        try:
            for i in list(self.bot.extensions):
                _log.info(f'Reloading {i}...')
                try:
                    self.bot.reload_extension(i)
                except commands.ExtensionFailed as e:
                    # FIXME: Workaround to avoid exception during the custom commands reload.
                    if not isinstance(e.original, commands.CommandRegistrationError):
                        raise e
                    _log.error(f'Couldn\'t reload the cog {i}, skipping.')
        except commands.ExtensionFailed:
            _log.error(f'Couldn\'t reload the cog {i}.]')
            return await ctx.reply(l10n['error'].format(i=i), delete_after=5)
        await msg.edit(content=l10n['success'], delete_after=5)

    @commands.command()
    @commands.guild_only()
    @commands.is_owner()
    async def host_info(self, ctx: commands.Context):
        def get_commit_string(branch: str, commit_sha: str):
            repo_string_format = '{l10n_branch}: `{branch}`\n{l10n_commit_sha}: `{commit_sha}`'
            bot_commit_string = repo_string_format.format(
                l10n_branch = l10n["branch"],
                branch = branch,
                l10n_commit_sha = l10n["commit_sha"],
                commit_sha = commit_sha
                )
            return bot_commit_string

        l10n = localization(self.bot, ctx.guild.id)['anastellos']['technical']['host_info']
        mem = psutil.virtual_memory()
        mem_str = l10n['memory'].format(total=round(mem.total/(2**30), 1), used=round(mem.used/(2**30), 1), used_percent=round(mem.used/mem.total*100))

        sys_info = platform.uname()
        sys_str = f'{sys_info.system}{" NT" if psutil.WINDOWS else " "+sys_info.release} {sys_info.version} {sys_info.machine}'

        uptime = time.gmtime(time.time() - self.bot.startup_time)
        uptime_str = f'{uptime.tm_hour}:{uptime.tm_min:02d}:{uptime.tm_sec:02d}'
        if uptime.tm_yday == 2:
            uptime_str = f'{uptime.tm_yday-1} {l10n["day"]} {uptime_str}'
        elif uptime.tm_yday > 2:
            uptime_str = f'{uptime.tm_yday-1} {l10n["days"]} {uptime_str}'

        fields = [
            (l10n['os'], sys_str),
            (l10n['mem'], mem_str),
            (l10n['python_ver'], sys.version),
            (l10n['nextcord_ver'], nextcord.__version__),
            (l10n['bot_uptime'], uptime_str)
        ]

        try:
            bot_repo_prefix = '.git/'
            bot_commit_details = get_commit_details(bot_repo_prefix)
            bot_commit_string = get_commit_string(*bot_commit_details)
            fields.append((l10n['bot_repo'], bot_commit_string))
        except Exception as e:
            _log.debug(f'{ctx.command.name} couldn\'t retrieve bot repository info.', exc_info=1)

        try:
            if os.path.exists('.git/modules/anastellos/'): engine_repo_prefix = '.git/modules/anastellos/'
            elif os.path.exists('anastellos/.git/'): engine_repo_prefix = 'anastellos/.git/'
            else: engine_repo_prefix = '.git/'
            engine_commit_details = get_commit_details(engine_repo_prefix)
            engine_commit_string = get_commit_string(*engine_commit_details)
            fields.append((l10n['engine_repo'], engine_commit_string))
        except Exception as e:
            _log.debug(f'{ctx.command.name} couldn\'t retrieve engine repository info.', exc_info=1)

        embed = AEEmbed(self.bot,
                        title=l10n['title'],
                        fields=fields)

        await ctx.reply(embed=embed)

    @commands.command(aliases=('latency',), hidden=False)
    @commands.guild_only()
    async def ping(self, ctx: commands.Context):
        msg1 = 'Ping...'
        time1 = default_timer()
        msg = await ctx.send(msg1)
        time2 = default_timer()
        latency = round((time2 - time1)*1000)
        msg2 = f'Pong! | {latency}ms'
        await msg.edit(content=msg2)
        _log.debug(f'{ctx.author} pinged the bot @ #{ctx.channel} ({ctx.guild}). Latency: {latency}ms.')

    @commands.command(hidden=False)
    @commands.check_any(
        commands.is_owner(),
        commands.has_guild_permissions(manage_guild=True)
    )
    async def leave(self, ctx: commands.Context):
        class LeaveMessageUI(nextcord.ui.View):
            def __init__(self, ctx: commands.Context, l10n: dict):
                super().__init__(timeout=180)
                self.ctx = ctx
                self.l10n = l10n
                self.add_item(self.LeaveButton(self.l10n['leave']))
                self.add_item(self.PurgeLeaveButton(
                    self.l10n['purge'], style=nextcord.ButtonStyle.danger))
                self.add_item(self.BaseLeaveButton(
                    self.l10n['cancel'], style=nextcord.ButtonStyle.primary))

            async def on_timeout(self):
                for item in self.children:
                    item.disabled = True
                await self.message.edit(view=self, embed=self.message.embeds[0])
                return None

            async def stop(self):
                await self.on_timeout()
                return super().stop()

            async def interaction_check(self, interaction: nextcord.Interaction):
                return self.ctx.author == interaction.user

            class BaseLeaveButton(nextcord.ui.Button):
                def __init__(self, l10n: dict, style: nextcord.ButtonStyle = nextcord.ButtonStyle.secondary):
                    self.l10n = l10n
                    super().__init__(label=self.l10n['label'], style=style)

                async def callback(self, interaction: nextcord.Interaction):
                    embed = interaction.message.embeds[0]
                    embed.title = self.l10n['title'].format(
                        name=interaction.client.config.name)
                    embed.description = self.l10n['desc']
                    _LeaveMessageUI.message = await interaction.message.edit(embed=embed)
                    await interaction.response.defer(ephemeral=True, with_message=False)
                    await self.view.stop()
                    return

            class LeaveButton(BaseLeaveButton):
                async def callback(self, interaction: nextcord.Interaction):
                    guild = interaction.guild
                    await super().callback(interaction)
                    _log.debug(f'{interaction.user.name}#{interaction.user.discriminator} made {interaction.client.config.name} to leave a guild.')
                    await guild.leave()
                    return

            class PurgeLeaveButton(BaseLeaveButton):
                async def callback(self, interaction: nextcord.Interaction):
                    interaction.client.guild_config.delete_guild_entry(
                        interaction.guild.id)
                    guild = interaction.guild
                    await super().callback(interaction)
                    _log.debug(f'{interaction.user.name}#{interaction.user.discriminator} made {interaction.client.config.name} to leave and forget a guild.')
                    await guild.leave()
                    return

        l10n = localization(self.bot, guild_id=ctx.guild.id)[
            'anastellos']['settings']['leave']
        emb1 = AEEmbed(self.bot, title=l10n['title_msg'].format(
            name=self.bot.config.name), desc=l10n['desc_msg'], colour=nextcord.Color.brand_red())
        _LeaveMessageUI = LeaveMessageUI(ctx, l10n['ui'])
        msg = await ctx.reply(embed=emb1, view=_LeaveMessageUI)
        _LeaveMessageUI.message = msg


def setup(bot):
    bot.add_cog(Technical(bot))
