# Susu group manager

A small command-line program that manages **one** rotating savings group (susu).
Every member pays the same fixed weekly amount (in GHS). Each week the whole
pot goes to one member, in the order they joined.

Pure Python 3.8+, **no third-party dependencies**.

## Run it

From the repository root:

```bash
python3 -m susu init --amount 50.00      # create the group
python3 -m susu add Ama                  # add members (joining order = payout order)
python3 -m susu add Kofi
python3 -m susu add Esi
python3 -m susu pay Ama 50               # record a contribution (partial is fine)
python3 -m susu pay Kofi 50
python3 -m susu pay Esi 30
python3 -m susu close                    # Esi owes 20.00 -> nothing is paid out
python3 -m susu pay Esi 20
python3 -m susu close                    # Ama receives GHS 150.00, week 2 begins
python3 -m susu report                   # week, who paid / owes, payout history
```

| Command | What it does |
|---|---|
| `init --amount 50.00 [--force]` | Create the group. Refuses to overwrite unless `--force`. |
| `add NAME` | Add a member (only before the first contribution). Use quotes for names with spaces. |
| `pay NAME AMOUNT [--week N]` | Record a payment for the **current** week. |
| `close` | Close the week. Pays the next member only if everyone paid in full; otherwise lists who owes what. |
| `report` | Current week, who has paid in full, who owes what, payout history. |

The group is saved in `susu.json` in the current directory. Use
`-f other.json` (before the command) or the `SUSU_FILE` environment variable to
choose another file, e.g. `python3 -m susu -f ama-group.json report`.

Errors print `Error: ...` to stderr and exit with code 1; the saved group is
never changed by a rejected command.

## Run the tests

```bash
python3 -m unittest discover -v
```

(`pytest` also works if you have it installed, but is not required.)

The suite has 37 tests, including the partial-payment case and the
"week cannot close" case, the full example from the brief, every validation
rule, persistence, and end-to-end CLI runs.

## Project layout

```
susu/
  money.py     exact money: text <-> integer pesewas
  errors.py    all user-facing exception types
  group.py     the domain rules (members, contributions, closing a week)
  storage.py   atomic JSON save/load with consistency checks
  report.py    turns results into text
  cli.py       argparse commands (thin: parse -> call Group -> print)
tests/         unit tests per layer + end-to-end CLI tests
NOTES.md       assumptions, decisions, and what I would improve
```

The rules live only in `group.py`; the CLI and storage have no business logic,
so a small API could be added on top without touching the rules.
