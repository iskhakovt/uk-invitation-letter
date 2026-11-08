import argparse
import os
import pathlib
import sys
from collections.abc import Sequence
from typing import Final

from .builder import BuildError, Engine, build
from .template import load_template_yaml

# Sets the default for `render --engine`, so a packager that bundles one engine
# can make it the default while a user's own setting, or the flag, still wins.
ENGINE_ENV: Final[str] = "UK_INVITATION_LETTER_ENGINE"


def _default_engine(parser: argparse.ArgumentParser) -> Engine:
    value = os.environ.get(ENGINE_ENV, "")
    if not value:
        return Engine.XELATEX
    try:
        return Engine(value)
    except ValueError:
        parser.error(f"{ENGINE_ENV}: invalid choice: {value!r} (choose from {', '.join(Engine)})")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="uk-invitation-letter", description="Generate a UK invitation letter")
    subparsers = parser.add_subparsers(dest="command", required=True)

    render = subparsers.add_parser("render", help="Render an invitation PDF from a data file")
    render.add_argument("--data", type=pathlib.Path, required=True, help="Invitation data file path")
    render.add_argument("--output", type=pathlib.Path, required=True, help="Output PDF path")
    render.add_argument(
        "--engine",
        type=Engine,
        choices=tuple(Engine),
        help=f"TeX engine (default: ${ENGINE_ENV} if set, else xelatex). xelatex, lualatex and pdflatex run "
        "through latexmk; tectonic is self-contained and fetches packages itself.",
    )

    subparsers.add_parser("gen", help="Print a template data.yml to stdout")

    args = parser.parse_args(argv)
    if args.command == "render" and args.engine is None:
        args.engine = _default_engine(render)
    try:
        if args.command == "render":
            build(args.data, args.output, args.engine)
        elif args.command == "gen":
            sys.stdout.write(load_template_yaml())
    except (BuildError, OSError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
