"""Jinja filters that turn model values into LaTeX.

The model describes the data and knows nothing about LaTeX; everything that
produces markup, escaping, non-breaking spaces or name joining, lives here.
Every filter returns `Tex`, which the template environment passes through
unescaped (see builder.py).
"""

from collections.abc import Callable, Mapping, Sequence
from typing import Final

from .util import Tex, and_join, date_format, phone_format, tex_nobreak


def nobreak(text: str) -> Tex:
    """A short phrase such as a name, kept on one line."""
    return tex_nobreak(text)


def names(full_names: Sequence[str]) -> Tex:
    """Full names joined with `and`, e.g. `Joseph~Brodsky and Maria~Sozzani`."""
    return Tex(and_join([tex_nobreak(name) for name in full_names]))


def first_names(full_names: Sequence[str]) -> Tex:
    """First names joined with `and`, e.g. `Joseph and Maria`."""
    return Tex(and_join([tex_nobreak(name.split(" ")[0]) for name in full_names]))


def address_inline(lines: Sequence[str]) -> Tex:
    """Address lines on one line, separated by commas."""
    return Tex(", ".join(tex_nobreak(line) for line in lines))


def address_block(lines: Sequence[str]) -> Tex:
    """Address lines separated by LaTeX line breaks."""
    return Tex("\\\\\n".join(tex_nobreak(line) for line in lines))


FILTERS: Final[Mapping[str, Callable[..., Tex]]] = {
    "nobreak": nobreak,
    "names": names,
    "first_names": first_names,
    "address_inline": address_inline,
    "address_block": address_block,
    "date": date_format,
    "phone": phone_format,
}
