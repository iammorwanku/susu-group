# Notes

## Assumptions (things the brief did not say)

1. **Adding members after the group has started is not allowed.** The group
   "starts" when the first contribution is recorded (or a payout is made).
   Adding someone later would change the pot size and the order halfway
   through the cycle, making earlier weeks unfair. All members must be added
   first.
2. **At least 2 members are needed** before payments can be recorded or a week
   closed. A rotation with one person is meaningless.
3. **Contributions can only be recorded for the current week.** `--week` is
   optional; if given it must equal the current week, otherwise it is rejected.
   This also means a week cannot be "left behind" with money still owed: it
   must be settled before it can be closed.
4. **One cycle.** Each member receives the pot exactly once. After the last
   member is paid, the group is *complete* and refuses further payments or
   closes. (Starting a new cycle is listed under improvements.)
5. **The pot is `weekly amount x number of members`**, and the recipient
   never "skips" paying: the recipient pays their share like everyone else,
   matching the brief's example (Ama pays 50 in week 1 and receives 150).
6. **Names are unique ignoring case and extra spaces.** `ama`, `AMA` and
   ` Ama ` are the same person. The original spelling is stored and shown.
   Names must be non-empty and at most 50 characters.
7. **Amounts have at most 2 decimal places.** `1.005` is rejected rather than
   silently rounded. No thousands separators, no scientific notation.
8. **A member who has already paid in full cannot pay again** that week (it is
   treated as an overpayment).
9. **Closing a week that cannot close is not an error.** It exits with code 0,
   prints who owes what, and changes nothing. Invalid input is exit code 1.
10. Currency is GHS and fixed.

## Decisions

- **Money is integer pesewas everywhere** (`50.00` -> `5000`). No floats, and
  floats are explicitly rejected at the boundary. Parsing uses a strict
  regex + `Decimal`, so there is nothing to round. Formatting uses `divmod`.
- **Layered design.** `Group` holds the rules and knows nothing about files or
  printing; `storage`, `report` and `cli` are thin edges. That keeps the rules
  easy to test (most tests never touch a file) and easy to reuse in an API.
- **Validate first, then mutate.** Every check in `record_contribution` happens
  before any state changes, so a rejected command leaves the group untouched
  (there is a test for this).
- **State is a JSON file**, written atomically (temp file + `os.replace`) and
  validated on load, so a crash or hand-edited file cannot silently corrupt
  money. The load check re-derives what must be true (payout order, pot size,
  week number) and rejects the file if it is not.
- **CLI with a saved file** rather than an interactive menu, so each action is
  scriptable and the end-to-end tests are simple.
- **Standard library only**, so there is nothing to install.
- **Git history** follows the build order: money -> members -> weekly rules ->
  persistence -> CLI -> docs, each commit with its own tests.

## What I would improve with more time

- **Start a new cycle** after completion (optionally with new members).
- **Late payments for past weeks / grace rules**, and an audit log of every
  contribution (who, when, how much) rather than only running totals.
- **Support a payout order that can be changed before the group starts**
  (e.g. draw lots, or swap two members).
- **Removing a member / handling a member who drops out** mid-cycle, which
  needs a real policy (refund? reassign their turn?).
- **Multiple groups** in one store, and a small HTTP API on top of `Group`.
- **File locking** so two terminals cannot write the same file at once.
- **More tests**: property-based tests (random payments never break the
  "money in = pot out" invariant), and a larger CLI test matrix.
- **Currency/locale formatting** (thousands separators, other currencies).
