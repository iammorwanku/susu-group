"""Command-line interface: python -m susu <command>."""
from __future__ import annotations

import argparse
import os
import sys

from . import storage
from .errors import SusuError
from .group import Group
from .money import to_pesewas
from .report import format_close_result, format_report, money

DEFAULT_FILE = "susu.json"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="susu", description="Manage one rotating savings group (susu), in GHS."
    )
    parser.add_argument(
        "-f", "--file",
        default=os.environ.get("SUSU_FILE", DEFAULT_FILE),
        help=f"where the group is saved (default: {DEFAULT_FILE}, or $SUSU_FILE)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init", help="create a group with a fixed weekly contribution")
    init.add_argument("--amount", required=True, help="weekly amount in GHS, e.g. 50.00")
    init.add_argument("--force", action="store_true", help="overwrite an existing group")

    add = sub.add_parser("add", help="add a member (joining order = payout order)")
    add.add_argument("name")

    pay = sub.add_parser("pay", help="record a (possibly partial) contribution")
    pay.add_argument("name")
    pay.add_argument("amount", help="amount in GHS, e.g. 30.00")
    pay.add_argument("--week", type=int, help="week number (must be the current week)")

    sub.add_parser("close", help="close the week; pays out only if everyone has paid")
    sub.add_parser("report", help="show current week, balances and payout history")
    return parser


def cmd_init(args, out) -> int:
    if storage.exists(args.file) and not args.force:
        raise SusuError(
            f"'{args.file}' already exists. Use --force to replace it, or -f to use another file."
        )
    group = Group(to_pesewas(args.amount))
    storage.save(args.file, group)
    print(f"Created a susu group: {money(group.weekly_amount)} per member per week.", file=out)
    return 0


def cmd_add(args, out) -> int:
    group = storage.load(args.file)
    name = group.add_member(args.name)
    storage.save(args.file, group)
    print(f"Added {name} as member #{len(group.members)}.", file=out)
    return 0


def cmd_pay(args, out) -> int:
    group = storage.load(args.file)
    amount = to_pesewas(args.amount)
    member = group.find_member(args.name)
    remaining = group.record_contribution(member, amount, args.week)
    storage.save(args.file, group)
    line = f"Recorded {money(amount)} from {member} for week {group.week}."
    if remaining:
        line += f" {member} still owes {money(remaining)}."
    else:
        line += f" {member} has paid in full."
    print(line, file=out)
    return 0


def cmd_close(args, out) -> int:
    group = storage.load(args.file)
    result = group.close_week()
    if result.closed:
        storage.save(args.file, group)
    print(format_close_result(group, result), file=out)
    return 0


def cmd_report(args, out) -> int:
    print(format_report(storage.load(args.file)), file=out)
    return 0


COMMANDS = {
    "init": cmd_init, "add": cmd_add, "pay": cmd_pay,
    "close": cmd_close, "report": cmd_report,
}


def main(argv=None, out=None, err=None) -> int:
    out = out or sys.stdout
    err = err or sys.stderr
    args = build_parser().parse_args(argv)
    try:
        return COMMANDS[args.command](args, out)
    except SusuError as exc:
        print(f"Error: {exc}", file=err)
        return 1
