from enum import Enum, EnumMeta

class EnumContainsMeta(EnumMeta):

    def __contains__(cls, value):
        try:
            cls(value)
        except ValueError:
            return False
        return True

class EnumContains(Enum, metaclass=EnumContainsMeta):
    pass
