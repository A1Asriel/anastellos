import logging
from datetime import datetime
from typing import Optional

import nextcord
from nextcord.ext import commands

from ..classes import AEEmbed, AnastellosBot, AnastellosInternalCog
from ..utils import localization

_log = logging.getLogger(__name__)


def accept_agreement(bot: AnastellosBot, guild: nextcord.Guild, lang: str = 'en') -> None:
    guild_cfg = bot.guild_config.create_guild_cfg(guild.id)
    guild_cfg.is_eula_accepted = True
    guild_cfg.lang = lang
    guild_cfg.save()
    _log.info(f'An admin of {guild.name} has accepted the agreement.')
    return None


class Privacy(AnastellosInternalCog):
    def cog_check(self, ctx: commands.Context) -> bool:
        return self.bot.config.demand_agreement

    class AgreementView(nextcord.ui.View):
        def __init__(self, l10n: dict, author: nextcord.Member, lang: str):
            super().__init__(timeout=300)
            self.l10n = l10n
            self.add_item(self.AgreeButton(self.l10n, author, lang))
            self.add_item(self.DeclineButton(self.l10n, author))

        class AgreeButton(nextcord.ui.Button):
            def __init__(self, l10n: dict, author: nextcord.Member, lang: str):
                super().__init__(
                    label=l10n['agree'], emoji='✅', style=nextcord.ButtonStyle.green)
                self.author = author
                self.lang = lang

            async def callback(self, interaction: nextcord.Interaction):
                if self.author.id != interaction.user.id:
                    return
                bot: AnastellosBot = interaction.client
                accept_agreement(bot, interaction.guild, self.lang)
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
    async def privacy(self, ctx: commands.Context, lang: str = 'en', confirmation: Optional[str] = None):
        if lang not in self.bot.config.lang_names or localization(self.bot, lang=lang)['anastellos'].get('privacy', {}).get('privacy') is None:
            lang = 'en'
        l10n = localization(self.bot, lang=lang)[
            'anastellos']['privacy']['privacy']
        title = l10n['title']
        desc = l10n['desc']
        creator = await self.bot.fetch_user(self.bot.owner_id)
        footer_title = l10n['footer'].format(creator=creator)
        url = l10n.get(
            '_url', 'https://a1asriel.github.io/AsrielBot-site/privacy.html')
        embed = AEEmbed(self.bot,
                        title=title,
                        desc=desc,
                        footer_title=footer_title,
                        url=url,
                        timestamp=datetime.fromtimestamp(l10n['timestamp']))

        if not ctx.author.guild_permissions.manage_guild or self.bot.guild_config.get_guild_cfg(ctx.guild.id) is not None and self.bot.guild_config.get_guild_cfg(ctx.guild.id).is_eula_accepted:
            await ctx.send(embed=embed)
            return None
        if confirmation != 'accept':
            await ctx.send(embed=embed, view=self.AgreementView(l10n, ctx.author, lang))
            return None
        accept_agreement(self.bot, ctx.guild, lang)
        try:
            await ctx.message.add_reaction('✅')
        except:
            pass
        return None


def setup(bot):
    bot.add_cog(Privacy(bot))
