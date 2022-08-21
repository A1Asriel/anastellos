from datetime import datetime
import nextcord
from nextcord.ext import commands

from ..classes import AEEmbed, AnastellosBot, AnastellosInternalCog
from ..utils import *


class Privacy(AnastellosInternalCog):
    def cog_check(self, ctx):
        return True


    class AgreementView(nextcord.ui.View):
        def __init__(self):
            super().__init__(timeout=300)
        
        @nextcord.ui.button(
            emoji='✅',
            style=nextcord.ButtonStyle.green
        )
        async def agree(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
            bot: AnastellosBot = interaction.client
            guild_cfg = bot.guild_config.get_guild_cfg(interaction.guild.id)
            guild_cfg.is_eula_accepted = True
            guild_cfg.save()
            for i in range(len(self.children)):
                self.children[i].disabled = True
            await interaction.message.edit(view=None)

        @nextcord.ui.button(
            emoji='❎',
            style=nextcord.ButtonStyle.red
        )
        async def not_agree(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
            try:
                await interaction.delete_original_message()
            except:
                pass
            await interaction.guild.leave()


    @commands.command()
    @commands.guild_only()
    async def privacy(self, ctx: commands.Context):
        l10n = localization(self.bot, guild_id=ctx.guild.id)['anastellos']['privacy']['privacy']
        title = l10n['title']
        desc = l10n['desc']
        creator = await self.bot.fetch_user(296735247213789215)
        footer_title = l10n['footer'].format(creator=creator)
        author_url = l10n.get('url', 'https://a1asriel.github.io/AsrielBot-site/privacy.html')
        await ctx.send(embed=AEEmbed(self.bot,
                                     title=title,
                                     desc=desc,
                                     footer_title=footer_title,
                                     author_url=author_url,
                                     timestamp=datetime.fromtimestamp(1661115600)),
                       view=self.AgreementView()
                       )


def setup(bot):
    bot.add_cog(Privacy(bot))
