import argparse
import pathlib
import sys

from .builder import ENGINES, build
from .template import TEMPLATE_YAML


def main() -> None:
    parser = argparse.ArgumentParser(prog="uk-invitation-letter", description="Generate a UK invitation letter")
    subparsers = parser.add_subparsers(dest="command", required=True)

    render = subparsers.add_parser("render", help="Render an invitation PDF from a data file")
    render.add_argument("--data", type=pathlib.Path, required=True, help="Invitation data file path")
    render.add_argument("--output", type=pathlib.Path, required=True, help="Output PDF path")
    render.add_argument("--engine", choices=ENGINES, default="xelatex", help="LaTeX engine (default: xelatex)")

    subparsers.add_parser("gen", help="Print a template data.yml to stdout")

    args = parser.parse_args()
    if args.command == "render":
        build(args.data, args.output, args.engine)
    elif args.command == "gen":
        sys.stdout.write(TEMPLATE_YAML)


if __name__ == "__main__":
    main()
