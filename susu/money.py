"""Exact money handling.

All money inside the program is an ``int`` number of pesewas (1 GHS = 100
pesewas), so there is never any floating point rounding. Text typed by a
person is converted once, at the edge, by ``to_pesewas``; ``format_pesewas``
turns it back into text for display.
"""
import re
from decimal import Decimal

from .errors import InvalidAmount

PESEWAS_PER_CEDI = 100

# Optional minus sign, whole part, optional 1-2 decimal places. No exponents,
# no thousands separators, no more than two decimals (we never round silently).
_AMOUNT_RE = re.compile(r"^-?\d{1,12}(\.\d{1,2})?$")


def to_pesewas(value) -> int:
    """Convert '50', '50.00' or '0.1' (str/int) to an exact int of pesewas.

    Floats and bools are refused on purpose: a float such as 0.1 is already
    inexact before we ever see it. Negative values parse fine here; the domain
    layer is what rejects them.
    """
    if isinstance(value, (bool, float)):
        raise InvalidAmount(
            "Amounts must be given as text like '50.00', not as a float."
        )
    if isinstance(value, int):
        return value * PESEWAS_PER_CEDI
    text = str(value).strip()
    if not _AMOUNT_RE.match(text):
        raise InvalidAmount(
            f"'{text}' is not a valid amount. Use a number such as 50 or 50.00 "
            "(at most 2 decimal places)."
        )
    return int(Decimal(text) * PESEWAS_PER_CEDI)


def format_pesewas(pesewas: int) -> str:
    """Format an int of pesewas as a plain two-decimal string, e.g. '150.00'."""
    sign = "-" if pesewas < 0 else ""
    whole, fraction = divmod(abs(pesewas), PESEWAS_PER_CEDI)
    return f"{sign}{whole}.{fraction:02d}"
