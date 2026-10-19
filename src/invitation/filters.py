"""Jinja filters that turn model values into LaTeX.

The model describes the data and knows nothing about LaTeX; everything that
produces markup (escaping, non-breaking spaces, name joining, date and phone
formatting) lives here. Every filter returns `Tex`, which the template
environment passes through unescaped (see builder.py).
"""

import datetime
from collections.abc import Callable, Mapping, Sequence
from typing import Final

import phonenumbers

from .util import Tex, parse_phone, tex_nobreak, use_non_breaking_space


def _strings(value: Sequence[str]) -> Sequence[str]:
    # A `str` is itself a `Sequence[str]`, so `{{ inviter.name|names }}` would
    # otherwise be joined letter by letter. Scalars take `|nobreak`.
    if isinstance(value, str):
        raise TypeError("expected a sequence of strings, got a single string; use the `nobreak` filter for one value")
    return value


def _and_join(items: Sequence[str]) -> str:
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f"{items[0]} and {items[1]}"
    return ", ".join(items[:-1]) + ", and~" + items[-1]


def names(full_names: Sequence[str]) -> Tex:
    """Full names joined with `and`, e.g. `Joseph~Brodsky and Maria~Sozzani`."""
    return Tex(_and_join([tex_nobreak(name) for name in _strings(full_names)]))


def first_names(full_names: Sequence[str]) -> Tex:
    """First names joined with `and`, e.g. `Joseph and Maria`."""
    # `split()` drops some control characters that pydantic's strip keeps, so a
    # name that is only those would split to nothing; fall back to the name.
    return Tex(_and_join([tex_nobreak((name.split() or [name])[0]) for name in _strings(full_names)]))


def address_inline(lines: Sequence[str]) -> Tex:
    """Address lines on one line, separated by commas."""
    return Tex(", ".join(tex_nobreak(line) for line in _strings(lines)))


def address_block(lines: Sequence[str]) -> Tex:
    """Address lines separated by LaTeX line breaks."""
    return Tex("\\\\\n".join(tex_nobreak(line) for line in _strings(lines)))


# Hard-coded so month names don't depend on the host's LC_TIME (strftime("%B")
# is locale-coupled). Babel would solve it with CLDR data but costs ~10 MB for
# one locale — the product only ever emits British English.
_MONTHS: Final[tuple[str, ...]] = (
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
)


def date(value: datetime.date) -> Tex:
    """`5~January~2026`: day without a leading zero, month in British English."""
    return Tex(f"{value.day}~{_MONTHS[value.month - 1]}~{value.year}")


def phone(number: str) -> Tex:
    """UK national format with non-breaking spaces, e.g. `07758~888305`."""
    national = phonenumbers.format_number(parse_phone(number), phonenumbers.PhoneNumberFormat.NATIONAL)
    return Tex(use_non_breaking_space(national))


FILTERS: Final[Mapping[str, Callable[..., Tex]]] = {
    "nobreak": tex_nobreak,
    "names": names,
    "first_names": first_names,
    "address_inline": address_inline,
    "address_block": address_block,
    "date": date,
    "phone": phone,
}
