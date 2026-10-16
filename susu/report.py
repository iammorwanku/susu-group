"""Turn domain objects into text for the command line."""
from __future__ import annotations

from .group import CURRENCY, CloseResult, Group
from .money import format_pesewas


def money(pesewas: int) -> str:
    return f"{CURRENCY} {format_pesewas(pesewas)}"


def format_close_result(group: Group, result: CloseResult) -> str:
    if not result.closed:
        lines = [f"Week {result.week} cannot close. Still outstanding:"]
        lines += [f"  {name} owes {money(owed)}" for name, owed in result.owing.items()]
        return "\n".join(lines)
    payout = result.payout
    lines = [f"Week {payout.week} closed. {payout.member} receives {money(payout.amount)}."]
    if group.is_complete:
        lines.append("Every member has now received the pot. The cycle is complete.")
    else:
        lines.append(f"Week {group.week} begins. Next recipient: {group.next_recipient}.")
    return "\n".join(lines)


def format_report(group: Group) -> str:
    lines = [
        f"Susu group: {money(group.weekly_amount)} per member per week",
        f"Members ({len(group.members)}): {', '.join(group.members) or '(none)'}",
    ]
    if group.is_complete:
        lines.append(f"Status: cycle complete after {len(group.payouts)} weeks.")
    elif len(group.members) < 2:
        lines.append("Status: add at least 2 members before taking payments.")
    else:
        lines.append(
            f"Current week: {group.week} of {len(group.members)} | "
            f"Pot: {money(group.pot)} | Next recipient: {group.next_recipient}"
        )
        balances = group.balances()
        paid = [b for b in balances if b.paid_in_full]
        owing = [b for b in balances if not b.paid_in_full]
        lines.append("Paid in full:")
        lines += [f"  {b.name}" for b in paid] or ["  (nobody yet)"]
        lines.append("Owes:")
        lines += [
            f"  {b.name} owes {money(b.owes)} (paid {money(b.paid)})" for b in owing
        ] or ["  (nobody - the week is ready to close)"]
    lines.append("Payout history:")
    lines += [
        f"  Week {p.week}: {p.member} received {money(p.amount)}" for p in group.payouts
    ] or ["  (no payouts yet)"]
    return "\n".join(lines)
