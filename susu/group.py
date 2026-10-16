"""Domain model for a susu (rotating savings group).

The Group knows the rules and nothing else: no files, no printing, no parsing
of user text. All amounts are integer pesewas (see money.py).
"""
from __future__ import annotations

from dataclasses import dataclass

from .errors import (
    DuplicateMember,
    GroupComplete,
    InvalidAmount,
    InvalidName,
    MembersLocked,
    NotEnoughMembers,
    Overpayment,
    UnknownMember,
    WrongWeek,
)
from .money import format_pesewas

CURRENCY = "GHS"
MAX_NAME_LENGTH = 50
MIN_MEMBERS = 2  # a "rotation" with one person is meaningless


def _clean_name(name) -> str:
    """Trim and collapse inner whitespace so 'Ama  Mensah ' == 'Ama Mensah'."""
    return " ".join(str(name).split())


class Group:
    def __init__(self, weekly_amount: int):
        if isinstance(weekly_amount, bool) or not isinstance(weekly_amount, int):
            raise InvalidAmount("The weekly amount must be a whole number of pesewas.")
        if weekly_amount <= 0:
            raise InvalidAmount("The weekly contribution must be greater than zero.")
        self.weekly_amount = weekly_amount
        self.members: list[str] = []          # in joining order = payout order
        self.week = 1                          # the week currently open
        self.paid: dict[str, int] = {}         # this week's payments per member
        self.payouts: list[Payout] = []        # completed weeks

    # ---- members ---------------------------------------------------------

    @property
    def started(self) -> bool:
        """True once any money has been recorded or paid out."""
        return bool(self.payouts) or any(self.paid.values())

    def find_member(self, name) -> str:
        """Return the stored spelling of a member (case-insensitive lookup)."""
        wanted = _clean_name(name).casefold()
        for member in self.members:
            if member.casefold() == wanted:
                return member
        raise UnknownMember(f"Unknown member '{_clean_name(name)}'.")

    def add_member(self, name) -> str:
        """Add a member at the end of the payout order and return their name.

        Rule: members can only be added before the group has started (before
        the first contribution). Adding later would change the pot size and
        the order mid-cycle and make earlier weeks unfair.
        """
        clean = _clean_name(name)
        if not clean:
            raise InvalidName("A member name cannot be empty.")
        if len(clean) > MAX_NAME_LENGTH:
            raise InvalidName(f"A member name can be at most {MAX_NAME_LENGTH} characters.")
        if any(m.casefold() == clean.casefold() for m in self.members):
            raise DuplicateMember(f"'{clean}' is already in the group.")
        if self.started:
            raise MembersLocked(
                "Members can only be added before the first contribution is recorded."
            )
        self.members.append(clean)
        self.paid[clean] = 0
        return clean
