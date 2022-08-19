# import os
from timeit import default_timer

import nextcord
from nextcord.ext import commands

from ..checks import reply_or_send
from ..classes import AEEmbed, AnastellosCog
from ..utils import *


class Technical(AnastellosCog, command_attrs={'hidden': True}):
    @commands.command(aliases=('destroy',))
    @commands.guild_only()
    @commands.is_owner()
    async def stop(self, ctx: commands.Context):
        l10n = localization(guild_id=ctx.guild.id)[
            'anastellos']['technical']['stop']
        await ctx.reply(l10n)
        return await self.bot.close()

    # Unsafe to use, this command is deprecated and to be removed in the future.
    """ @commands.command(enabled=False)
    @commands.guild_only()
    @commands.is_owner()
    async def shutdown(self, ctx: commands.Context):
        l10n = localization(guild_id=ctx.guild.id)['anastellos']['technical']['shutdown']
        if self.bot.config.mode == 'indev':
            return await ctx.reply(l10n['error_indev'], delete_after=5)
        # if not self.bot.config.can_shutdown:
        #     return await ctx.reply(l10n['cant_shutdown'], delete_after=5)
        await ctx.reply(l10n['msg'])
        os.system('shutdown -s -t 10')
        return await self.bot.close() """

    @commands.command(hidden=True)
    @commands.guild_only()
    @commands.is_owner()
    async def reload(self, ctx: commands.Context):
        l10n = localization(guild_id=ctx.guild.id)[
            'anastellos']['technical']['reload']
        msg = await ctx.reply(l10n['start'], delete_after=5)
        i = '$modulename'
        try:
            for i in list(self.bot.extensions):
                print(f'[INFO] Reloading {i}...')
                try:
                    self.bot.reload_extension(i)
                except ExtensionFailed as e:
                    # FIXME: Workaround to avoid exception during the custom commands reload.
                    print(f'[ERROR] Couldn\'t reload the cog {i}, skipping.')
                    if not isinstance(e.original, commands.CommandRegistrationError):
                        raise e
        except ExtensionFailed:
            print(f'[ERROR Couldn\'t reload the cog {i}.]')
            return await ctx.reply(l10n['error'].format(i=i), delete_after=5)
        await msg.edit(content=l10n['success'], delete_after=5)

    @commands.command(aliases=('latency',))
    @commands.guild_only()
    async def ping(self, ctx: commands.Context):
        msg1 = 'Ping...'
        time1 = default_timer()
        msg = await ctx.send(msg1)
        time2 = default_timer()
        latency = round((time2 - time1)*1000)
        msg2 = f'Pong! | {latency}ms'
        await msg.edit(content=msg2)
        print(
            f'[DEBUG] {ctx.author} pinged the bot @ #{ctx.channel} ({ctx.guild}). Latency: {latency}ms.')

    @commands.command()
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
                    append = {'telemetry': 0}
                    write_config(
                        append=append, guildid=interaction.guild.id, filename='server_cfg')
                    guild = interaction.guild
                    await super().callback(interaction)
                    print(
                        f'[DEBUG] {interaction.user.name}#{interaction.user.discriminator} made {interaction.client.config.name} to leave a guild.')
                    await guild.leave()
                    return

            class PurgeLeaveButton(BaseLeaveButton):
                async def callback(self, interaction: nextcord.Interaction):
                    delete_guild_config(interaction.guild.id, 'server_cfg')
                    guild = interaction.guild
                    await super().callback(interaction)
                    print(
                        f'[DEBUG] {interaction.user.name}#{interaction.user.discriminator} made {interaction.client.config.name} to leave and forget a guild.')
                    await guild.leave()
                    return

        l10n = localization(guild_id=ctx.guild.id)[
            'anastellos']['settings']['leave']
        emb1 = AEEmbed(self.bot, title=l10n['title_msg'].format(
            name=self.bot.config.name), desc=l10n['desc_msg'], colour=nextcord.Color.brand_red())
        _LeaveMessageUI = LeaveMessageUI(ctx, l10n['ui'])
        msg = await ctx.reply(embed=emb1, view=_LeaveMessageUI)
        _LeaveMessageUI.message = msg


def setup(bot):
    bot.add_cog(Technical(bot))
