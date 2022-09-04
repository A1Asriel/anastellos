from inspect import Parameter
from itertools import zip_longest

from nextcord.ext import commands

from anastellos.checks import is_eula_accepted

from .classes import AEEmbed
from .utils import localization


class AEHelpCommand(commands.HelpCommand):
    def __init__(self, **options):
        super().__init__(**options)

    def copy(self):  # This fixes the check disappearance.
        obj = self.__class__(*self.__original_args__, **
                             self.__original_kwargs__)  # type: ignore
        obj._command_impl = self._command_impl
        self.add_check(is_eula_accepted)
        return obj

    def get_command_signature(self, command: commands.Command):
        l10n: dict = localization(self.context.bot, self.context.guild.id)[
            'anastellos']['info']['help']['commands'].get(command.name, dict())
        if command.parent:
            alias = self.context.clean_prefix + command.full_parent_name + ' ' + command.name
        else:
            alias = self.context.clean_prefix + command.name
        if command.aliases:
            if command.parent:
                aliases = command.aliases
            else:
                aliases = [self.context.clean_prefix +
                           i for i in command.aliases]
            alias += ' | ' + ' | '.join(aliases)

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
            'anastellos']['info']['help']['commands'].get(command.name, dict())
        out = l10n.get('desc')
        extra = l10n.get('extra')
        if detailed:
            return out, extra
        return out

    async def send_command_help(self, command: commands.Command):
        l10n: dict = localization(self.context.bot, self.context.guild.id)[
            'anastellos']['info']['help']
        if not await command.can_run(self.context):
            raise commands.MissingPermissions
        signature = '`' + self.get_command_signature(command) + '`'
        description = self.get_command_description(command, detailed=True)
        if command.parent:
            embed_title = self.context.clean_prefix + \
                command.full_parent_name + ' ' + command.name
        else:
            embed_title = self.context.clean_prefix + command.name
        embed_desc = f'{l10n["usage"]}\n{signature}'
        if description[0]:
            embed_desc += f'\n{l10n["description"]}\n{description[0]}'
        if description[1]:
            embed_desc += f'\n{l10n["extra"]}\n{description[1]}'
        embed = AEEmbed(self.context.bot, title=embed_title, desc=embed_desc)
        await self.context.reply(embed=embed)

    async def send_bot_help(self, mapping):
        l10n: dict = localization(self.context.bot, self.context.guild.id)[
            'anastellos']['info']['help']
        bot: commands.Bot = self.context.bot
        embed_title = l10n['title']
        embed_description = l10n['desc']
        embed_fields = []
        commandlist = await self.filter_commands(bot.commands, sort=True)
        for command in commandlist:
            if not command.enabled or command.parent:
                continue
            field = [
                f'`{self.get_command_signature(command)}`', self.get_command_description(command)]
            embed_fields.append(field)
        embed = AEEmbed(self.context.bot, title=embed_title,
                        desc=embed_description, fields=embed_fields)
        await self.context.reply(embed=embed)

    async def send_group_help(self, group: commands.Group):
        l10n: dict = localization(self.context.bot, self.context.guild.id)[
            'anastellos']['info']['help']
        embed_title = l10n['title']
        if group.parent:
            embed_title = self.context.clean_prefix + \
                group.full_parent_name + ' ' + group.name
        else:
            embed_title = self.context.clean_prefix + group.name
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

    async def command_not_found(self, string):
        raise commands.CommandNotFound(string)
