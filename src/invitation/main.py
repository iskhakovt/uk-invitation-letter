import argparse
import pathlib
import sys
from collections.abc import Sequence

from .builder import ENGINES, BuildError, build
from .template import load_template_yaml


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="uk-invitation-letter", description="Generate a UK invitation letter")
    subparsers = parser.add_subparsers(dest="command", required=True)

    render = subparsers.add_parser("render", help="Render an invitation PDF from a data file")
    render.add_argument("--data", type=pathlib.Path, required=True, help="Invitation data file path")
    render.add_argument("--output", type=pathlib.Path, required=True, help="Output PDF path")
    render.add_argument(
        "--engine",
        choices=ENGINES,
        default="xelatex",
        help="TeX engine (default: xelatex). xelatex, lualatex and pdflatex run through latexmk; "
        "tectonic is self-contained and fetches packages itself.",
    )

    subparsers.add_parser("gen", help="Print a template data.yml to stdout")

    args = parser.parse_args(argv)
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
