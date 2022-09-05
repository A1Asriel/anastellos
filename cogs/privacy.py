from datetime import datetime

import nextcord
from nextcord.ext import commands

from ..classes import AEEmbed, AnastellosBot, AnastellosInternalCog
from ..utils import *


class Privacy(AnastellosInternalCog):
    def cog_check(self, ctx):
        return self.bot.config.demand_agreement

    class AgreementView(nextcord.ui.View):
        def __init__(self, l10n, author):
            super().__init__(timeout=300)
            self.l10n = l10n
            self.add_item(self.AgreeButton(self.l10n, author))
            self.add_item(self.DeclineButton(self.l10n, author))

        class AgreeButton(nextcord.ui.Button):
            def __init__(self, l10n, author):
                super().__init__(
                    label=l10n['agree'], emoji='✅', style=nextcord.ButtonStyle.green)
                self.author = author

            async def callback(self, interaction: nextcord.Interaction):
                if self.author.id != interaction.user.id:
                    return
                bot: AnastellosBot = interaction.client
                guild_cfg = bot.guild_config.create_guild_cfg(
                    interaction.guild.id)
                guild_cfg.is_eula_accepted = True
                guild_cfg.lang = interaction.guild.preferred_locale[
                    :2] if interaction.guild.preferred_locale is not None else guild_cfg.lang
                guild_cfg.save()
                await interaction.message.edit(view=None)

        class DeclineButton(nextcord.ui.Button):
            def __init__(self, l10n, author):
                super().__init__(
                    label=l10n['decline'], emoji='❎', style=nextcord.ButtonStyle.red)
                self.author = author

            async def callback(self, interaction: nextcord.Interaction):
                if self.author.id != interaction.user.id:
                    return
                try:
                    await interaction.delete_original_message()
                except:
                    pass
                await interaction.guild.leave()

    @commands.command()
    @commands.guild_only()
    async def privacy(self, ctx: commands.Context, lang='en'):
        if lang not in self.bot.config.lang_names or localization(None, lang=lang)['anastellos'].get('privacy', {}).get('privacy') is None:
            lang = 'en'
        l10n = localization(None, lang=lang)[
            'anastellos']['privacy']['privacy']
        title = l10n['title']
        desc = l10n['desc']
        creator = await self.bot.fetch_user(296735247213789215)
        footer_title = l10n['footer'].format(creator=creator)
        url = l10n.get(
            '_url', 'https://a1asriel.github.io/AsrielBot-site/privacy.html')
        embed = AEEmbed(self.bot,
                        title=title,
                        desc=desc,
                        footer_title=footer_title,
                        url=url,
                        timestamp=datetime.fromtimestamp(l10n['timestamp']))

        if (
            (self.bot.guild_config.get_guild_cfg(ctx.guild.id) is None or not self.bot.guild_config.get_guild_cfg(ctx.guild.id).is_eula_accepted) and
            nextcord.Permissions.manage_guild in ctx.author.guild_permissions
        ):
            await ctx.send(embed=embed, view=self.AgreementView(l10n, ctx.author))
        else:
            await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Privacy(bot))
