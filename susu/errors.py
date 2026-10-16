"""Exceptions raised by the susu program.

Every error derives from SusuError and carries a message that is safe to show
directly to the person using the program.
"""


class SusuError(Exception):
    """Base class for all expected, user-facing errors."""


class InvalidAmount(SusuError):
    """An amount is malformed, zero, negative or otherwise unusable."""


class InvalidName(SusuError):
    """A member name is empty or too long."""


class UnknownMember(SusuError):
    """The named member is not in the group."""


class DuplicateMember(SusuError):
    """A member with that name is already in the group."""


class Overpayment(SusuError):
    """A payment is larger than what the member still owes this week."""


class WrongWeek(SusuError):
    """A contribution was aimed at a week other than the current one."""


class MembersLocked(SusuError):
    """Members cannot be added once the group has started."""


class NotEnoughMembers(SusuError):
    """The group needs more members before it can take payments."""


class GroupComplete(SusuError):
    """Every member has already received the pot; the cycle is finished."""
