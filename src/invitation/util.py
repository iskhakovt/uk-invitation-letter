import re
from collections.abc import Mapping
from typing import Final

import phonenumbers


class Tex(str):
    """A string that is already valid LaTeX and must not be escaped again.

    Every `{{ ... }}` expression in a template is escaped automatically (see
    builder.py) unless it is a `Tex`. The Jinja filters in filters.py are the
    only producers of `Tex`; the model is plain data.

    Like any `str` subclass, string operations on it (`+`, `.upper()`, slicing,
    Jinja's built-in filters) return a plain `str`, which would then be escaped
    a second time. Transform text *before* escaping it. The escaping test in
    tests/test_builder.py asserts that no double-escaped sequence reaches the
    output of a letter whose every field contains special characters.
    """


_TEX_SPECIALS: Final[Mapping[str, str]] = {
    "\\": r"\textbackslash{}",
    "&": r"\&",
    "%": r"\%",
    "$": r"\$",
    "#": r"\#",
    "_": r"\_",
    "{": r"\{",
    "}": r"\}",
    "^": r"\textasciicircum{}",
    "~": r"\textasciitilde{}",
}
_TEX_SPECIALS_RE: Final[re.Pattern[str]] = re.compile("[" + re.escape("".join(_TEX_SPECIALS)) + "]")
_TEX_SPECIALS_BUT_TILDE_RE: Final[re.Pattern[str]] = re.compile(
    "[" + re.escape("".join(c for c in _TEX_SPECIALS if c != "~")) + "]"
)


def _escape(s: str, specials: re.Pattern[str]) -> str:
    return specials.sub(lambda m: _TEX_SPECIALS[m.group()], s)


def tex_escape(s: str) -> Tex:
    """Escape LaTeX special characters so free text renders literally."""
    if isinstance(s, Tex):
        return s
    return Tex(_escape(s, _TEX_SPECIALS_RE))


def tex_nobreak(s: str) -> Tex:
    """Escape a short phrase (a name, an address line) and keep its words on one line.

    Spaces become non-breaking. A `~` typed in the data file is kept as one too: that is
    the documented way to hold a two-word first name together in the `first_names` filter.
    Input that is already `Tex` is not escaped again but still gets its spaces made non-breaking.
    """
    if not isinstance(s, Tex):
        s = _escape(s, _TEX_SPECIALS_BUT_TILDE_RE)
    return Tex(use_non_breaking_space(s))


def parse_phone(phone: str) -> phonenumbers.PhoneNumber:
    """Parse a phone number, defaulting to UK dialling rules.

    Raises ValueError for text that is not a phone number or has the wrong number of digits.
    Range validity is deliberately not checked: the metadata lags new allocations, and the
    README example sits in Ofcom's reserved drama range.
    """
    try:
        number = phonenumbers.parse(phone, "GB")
    except phonenumbers.NumberParseException as e:
        raise ValueError(f"{phone!r} is not a phone number: {e}") from e
    reason = phonenumbers.is_possible_number_with_reason(number)
    if reason != phonenumbers.ValidationResult.IS_POSSIBLE:
        raise ValueError(f"{phone!r} is not a possible phone number (wrong number of digits?)")
    return number


def fix_floating_punctuation(s: str) -> str:
    return re.sub(r" +([,.;:!?])", r"\g<1>", s)


def use_non_breaking_space(s: str) -> str:
    return s.replace(" ", "~")
