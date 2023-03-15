from enum import Enum, EnumMeta


class EnumContainsMeta(EnumMeta):
    """ A new metaclass for Enum that implements __contains__"""

    def __contains__(cls, value):
        """ Determine if the value is a member of this Enum
        If the value can be casted against the class, it must be a member and
        viceversa.
        """
        try:
            cls(value)
            return True
        except ValueError:
            return False


class EnumContains(Enum, metaclass=EnumContainsMeta):
    pass
