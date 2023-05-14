from inspect import Parameter
from itertools import zip_longest
from typing import Union

from nextcord import Colour
from nextcord.ext import commands

from anastellos.checks import is_eula_accepted

from .classes import AEEmbed, AnastellosCog
from .utils import localization


class AEHelpCommand(commands.HelpCommand):
    def __init__(self, **options):
        super().__init__(**options)

    def copy(self):  # This fixes the check disappearance.
        self.add_check(is_eula_accepted)
        return super().copy()

    def get_command_signature(self, command: commands.Command):
        l10n: dict = localization(self.context.bot, self.context.guild.id)[
            'anastellos']['cogs'][command.cog_name.lower()]['commands'][command.name]['help']
        alias = f'{self.context.clean_prefix}{command.full_parent_name+" " if command.parent is not None else ""}{command.name}'
        if command.aliases:
            if command.parent:
                aliases = command.aliases
            else:
                aliases = [f'{self.context.clean_prefix}{i}' for i in command.aliases]
            alias += f' | {" | ".join(aliases)}'

        out = alias

        paramsdict = command.clean_params
        if paramsdict:
            params = []
            args: dict = l10n.get('args', dict())
            for paramobj, index in zip_longest(paramsdict, args):
                param = args.get(index, paramobj)
                if not paramsdict[paramobj].default is Parameter.empty:
                    if paramsdict[paramobj].default != '' and paramsdict[paramobj].default is not None:
                        param += f'={str(paramsdict[paramobj].default)}'
                    param = f'[{param}]'
                else:
                    param = f'<{param}>'
                params.append(param)
            params = ' '.join(params)
            out += ' ' + params
        return out

    def get_command_description(self, command: commands.Command, *, detailed=False):
        l10n: dict = localization(self.context.bot, self.context.guild.id)[
            'anastellos']['cogs'][command.cog_name.lower()]['commands'].get(command.name, dict()).get('help', dict())
        out = l10n.get('desc', '').format(def_prefix=self.context.bot.config.def_prefix, bot_name=self.context.bot.config.name)
        extra = l10n.get('extra', '').format(lang_names='`, `'.join(self.context.bot.l10n.lang_list))
        if detailed:
            return out, extra
        return out

    async def send_command_help(self, command: commands.Command):
        l10n: dict = localization(self.context.bot, self.context.guild.id)[
            'anastellos']['info']['help']
        if not await command.can_run(self.context):
            raise commands.MissingPermissions
        signature = f'`{self.get_command_signature(command)}`'
        description = self.get_command_description(command, detailed=True)
        embed_title = f'{self.context.clean_prefix}{command.full_parent_name+" " if command.parent is not None else ""}{command.name}'
        embed_desc = f'{l10n["usage"]}\n{signature}'
        if description[0]:
            embed_desc += f'\n{l10n["description"]}\n{description[0]}'
        if description[1]:
            embed_desc += f'\n{l10n["extra"]}\n{description[1]}'
        embed = AEEmbed(self.context.bot, title=embed_title, desc=embed_desc)
        await self.context.reply(embed=embed)

    async def send_cog_help(self, cog: AnastellosCog):
        l10n: dict = localization(self.context.bot, self.context.guild.id)[
            'anastellos']['help']
        bot: commands.Bot = self.context.bot
        embeds = []
        embed_commands_title = cog.qualified_name
        embed_commands_description = l10n['desc']

        commandlist = []
        grouplist = []
        for c in cog.walk_commands():
            if isinstance(c, commands.Group):
                grouplist.append(c)
            else:
                commandlist.append(c)
        commandlist = await self.filter_commands(commandlist, sort=True)
        grouplist = await self.filter_commands(grouplist, sort=True)

        embed_commands_fields = []
        for command in commandlist:
            if not command.enabled or command.parent:
                continue
            field = [f'`{self.get_command_signature(command)}`', self.get_command_description(command)]
            embed_commands_fields.append(field)
        embed_commands = AEEmbed(self.context.bot, title=embed_commands_title,
                                 desc=embed_commands_description, fields=embed_commands_fields)
        embeds.append(embed_commands)

        if grouplist:
            embed_groups_title = l10n['title_groups']
            embed_groups_description = l10n['desc_groups'].format(prefix=self.context.clean_prefix)
            embed_groups_fields = []
            for group in grouplist:
                if not group.enabled or group.parent:
                    continue
                field = [f'`{self.get_command_signature(group)}`', self.get_command_description(group)]
                embed_groups_fields.append(field)
            embed_groups = AEEmbed(bot, title=embed_groups_title,
                                   desc=embed_groups_description, fields=embed_groups_fields,
                                   author_name=None, author_icon=None)
            embeds.append(embed_groups)

        await self.context.reply(embeds=embeds)

    async def send_group_help(self, group: commands.Group):
        l10n: dict = localization(self.context.bot, self.context.guild.id)[
            'anastellos']['info']['help']
        embed_title = f'{self.context.clean_prefix}{group.full_parent_name+" " if group.parent is not None else ""}{group.name}'
        embed_fields = []
        commandlist = await self.filter_commands(group.commands, sort=True)
        for command in commandlist:
            if not command.enabled:
                continue
            field = [
                f'`{self.get_command_signature(command)}`', self.get_command_description(command)]
            embed_fields.append(field)
        embed = AEEmbed(self.context.bot, title=embed_title,
                        fields=embed_fields)
        await self.context.reply(embed=embed)

    async def send_bot_help(self, mapping):
        def valid_cog(cog: Union[AnastellosCog, str]) -> bool:
            if isinstance(cog, str):
                cog = self.context.bot.get_cog(cog)
            for cmd in cog.walk_commands():
                if cmd.enabled and not cmd.hidden:
                    return True
            return False

        l10n: dict = localization(self.context.bot, self.context.guild.id)[
            'anastellos']['help']
        guild_config = self.context.bot.guild_config.get_guild_cfg(self.context.guild.id)
        active_cogs = []
        inactive_cogs = []
        internal_cogs = []
        for cog_name in self.context.bot.cogs:
            cog = self.context.bot.get_cog(cog_name)
            if not valid_cog(cog):
                continue
            if '__type__' in cog.__dict__ and cog.__type__ == 'internal':
                internal_cogs.append(cog_name)
            elif cog_name not in guild_config.disabled_cogs:
                active_cogs.append(cog_name)
            else:
                inactive_cogs.append(cog_name)
        embeds = []
        embeds.append(AEEmbed(self.context.bot, title=l10n['internal_cogs'], desc='\n'.join(internal_cogs)))
        if active_cogs: embeds.append(AEEmbed(self.context.bot, title=l10n['active_cogs'], desc='\n'.join(active_cogs), author_name=None, author_icon=None, colour=Colour.brand_green()))
        if inactive_cogs: embeds.append(AEEmbed(self.context.bot, title=l10n['inactive_cogs'], desc='\n'.join(inactive_cogs), author_name=None, author_icon=None, colour=None))
        await self.context.reply(embeds=embeds)

    async def command_not_found(self, string):
        raise commands.CommandNotFound(string)
