"""
Constants defined by the core app
"""

from utils.const import EnumContains


class Sentinel(EnumContains):
    """Sentinels for telling an absent value apart from a falsy one.

    ``Sentinel.UNSET`` is used as a ``pop``/``get`` default so a missing key
    can be distinguished from a key whose stored value is ``False``.
    """

    UNSET = "unset"
