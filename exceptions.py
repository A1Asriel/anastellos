class AnastellosException(Exception):
    ...


class AnastellosInitError(AnastellosException):
    def __init__(self, message=None, **kwargs):
        for key, value in kwargs.items():
            self.__setattr__(key, value)
        super().__init__(message)
