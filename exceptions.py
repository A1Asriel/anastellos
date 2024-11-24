from typing import Iterable, Type
import nextcord
from nextcord.ext.commands import Command, CommandError


class AnastellosException(Exception):
    ...


class AnastellosInitError(AnastellosException):
    def __init__(self, message=None, **kwargs):
        for key, value in kwargs.items():
            self.__setattr__(key, value)
        super().__init__(message)


class AnastellosCommandError(AnastellosException, CommandError):
    ...

class AnastellosChannelTypeError(AnastellosCommandError):
    def __init__(self, allowed_types: Iterable[Type[nextcord.abc.Messageable]] = None, message=None, **kwargs):
        self.allowed_types = allowed_types if allowed_types is not None else []
        for key, value in kwargs.items():
            self.__setattr__(key, value)
        super().__init__(message)

class L10nUnsupported(AnastellosCommandError):
    def __init__(self, command: Command, l10n: str, **kwargs):
        self.l10n = l10n
        self.command = command
        self.message = f'Command {self.command.name} does not support {l10n} localization'
        super().__init__(self.message, **kwargs)
