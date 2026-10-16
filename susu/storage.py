"""Save and load a Group as a JSON file.

Amounts are stored as integer pesewas, so a save/load round trip is exact.
"""
from __future__ import annotations

import json
import os
import tempfile

from .errors import StorageError, SusuError
from .group import CURRENCY, Group, Payout

FORMAT_VERSION = 1


def group_to_dict(group: Group) -> dict:
    return {
        "version": FORMAT_VERSION,
        "currency": CURRENCY,
        "weekly_amount": group.weekly_amount,
        "week": group.week,
        "members": list(group.members),
        "paid": dict(group.paid),
        "payouts": [
            {"week": p.week, "member": p.member, "amount": p.amount}
            for p in group.payouts
        ],
    }


def group_from_dict(data: dict) -> Group:
    """Rebuild a Group, checking the data is internally consistent."""
    try:
        if data["version"] != FORMAT_VERSION:
            raise StorageError(f"Unsupported file version {data['version']!r}.")
        group = Group(data["weekly_amount"])
        group.members = [str(m) for m in data["members"]]
        group.paid = {m: data["paid"][m] for m in group.members}
        group.payouts = [
            Payout(p["week"], p["member"], p["amount"]) for p in data["payouts"]
        ]
        group.week = data["week"]
    except SusuError as exc:
        if isinstance(exc, StorageError):
            raise
        raise StorageError(f"The saved group is invalid: {exc}") from exc
    except (KeyError, TypeError, ValueError, AttributeError) as exc:
        raise StorageError(f"The saved group file is malformed ({exc!r}).") from exc
    _check_consistency(group)
    return group


def _check_consistency(group: Group) -> None:
    ints = [group.week, *group.paid.values(), *(p.amount for p in group.payouts)]
    if any(isinstance(v, bool) or not isinstance(v, int) for v in ints):
        raise StorageError("The saved group file contains non-integer numbers.")
    if len(set(m.casefold() for m in group.members)) != len(group.members):
        raise StorageError("The saved group file has duplicate members.")
    if any(not 0 <= v <= group.weekly_amount for v in group.paid.values()):
        raise StorageError("The saved group file has an impossible payment amount.")
    if len(group.payouts) > len(group.members):
        raise StorageError("The saved group file has more payouts than members.")
    for i, payout in enumerate(group.payouts):
        if (
            payout.week != i + 1
            or payout.member != group.members[i]
            or payout.amount != group.pot
        ):
            raise StorageError("The saved payout history does not match the rules.")
    expected_week = len(group.payouts) + (0 if group.is_complete else 1)
    if group.week != expected_week:
        raise StorageError("The saved week number does not match the payout history.")


def exists(path: str) -> bool:
    return os.path.exists(path)


def save(path: str, group: Group) -> None:
    """Write atomically so a crash mid-write cannot corrupt the saved group."""
    directory = os.path.dirname(os.path.abspath(path))
    fd, tmp = tempfile.mkstemp(dir=directory, prefix=".susu-", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(group_to_dict(group), handle, indent=2)
            handle.write("\n")
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def load(path: str) -> Group:
    if not os.path.exists(path):
        raise StorageError(
            f"No group found at '{path}'. Create one with: "
            "python -m susu init --amount 50.00"
        )
    try:
        with open(path, encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise StorageError(f"Could not read '{path}': {exc}") from exc
    return group_from_dict(data)
