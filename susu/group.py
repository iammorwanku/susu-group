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

    # ---- the weekly cycle ------------------------------------------------

    @property
    def is_complete(self) -> bool:
        """True when every member has received the pot once."""
        return bool(self.members) and len(self.payouts) == len(self.members)

    @property
    def pot(self) -> int:
        return self.weekly_amount * len(self.members)

    @property
    def next_recipient(self) -> str | None:
        if self.is_complete or not self.members:
            return None
        return self.members[len(self.payouts)]

    def _require_open_week(self) -> None:
        if self.is_complete:
            raise GroupComplete(
                "Every member has already received the pot; this cycle is finished."
            )
        if len(self.members) < MIN_MEMBERS:
            raise NotEnoughMembers(
                f"The group needs at least {MIN_MEMBERS} members before it can take payments."
            )

    def amount_owed(self, name) -> int:
        """What this member still owes for the current week."""
        return self.weekly_amount - self.paid[self.find_member(name)]

    def outstanding(self) -> dict[str, int]:
        """Members who have not paid in full this week -> amount still owed."""
        return {
            m: self.weekly_amount - self.paid[m]
            for m in self.members
            if self.paid[m] < self.weekly_amount
        }

    def balances(self) -> list[MemberStatus]:
        return [
            MemberStatus(m, self.paid[m], self.weekly_amount - self.paid[m])
            for m in self.members
        ]

    def record_contribution(self, name, amount: int, week: int | None = None) -> int:
        """Record a (possibly partial) payment. Returns what the member still owes.

        Rule: contributions can only be recorded for the current week. If a
        week is given and it is not the current one, the payment is refused.
        Nothing is changed when any check fails.
        """
        member = self.find_member(name)
        if isinstance(amount, bool) or not isinstance(amount, int):
            raise InvalidAmount("The amount must be a whole number of pesewas.")
        if amount <= 0:
            raise InvalidAmount("The amount must be greater than zero.")
        self._require_open_week()
        if week is not None and week != self.week:
            raise WrongWeek(
                f"Week {week} is not open. Contributions can only be recorded for "
                f"the current week ({self.week})."
            )
        owed = self.weekly_amount - self.paid[member]
        if owed == 0:
            raise Overpayment(f"{member} has already paid in full for week {self.week}.")
        if amount > owed:
            raise Overpayment(
                f"{member} only owes {format_pesewas(owed)} for week {self.week}; "
                f"cannot accept {format_pesewas(amount)}."
            )
        self.paid[member] += amount
        return owed - amount

    def close_week(self) -> CloseResult:
        """Try to close the current week.

        If everyone has paid in full, the pot goes to the next member in joining
        order and the next week opens. Otherwise nothing changes and the result
        lists who still owes what.
        """
        self._require_open_week()
        owing = self.outstanding()
        if owing:
            return CloseResult(False, self.week, None, owing)
        payout = Payout(self.week, self.members[len(self.payouts)], self.pot)
        self.payouts.append(payout)
        self.paid = {m: 0 for m in self.members}
        if not self.is_complete:
            self.week += 1
        return CloseResult(True, payout.week, payout, {})


@dataclass(frozen=True)
class Payout:
    week: int
    member: str
    amount: int


@dataclass(frozen=True)
class MemberStatus:
    name: str
    paid: int
    owes: int

    @property
    def paid_in_full(self) -> bool:
        return self.owes == 0


@dataclass(frozen=True)
class CloseResult:
    closed: bool
    week: int                    # the week that was attempted
    payout: Payout | None        # set only when closed
    owing: dict[str, int]        # set only when not closed
