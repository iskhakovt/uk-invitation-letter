import argparse
import pathlib

from .builder import build


def main() -> None:
    parser = argparse.ArgumentParser(prog="uk-invitation-letter", description="Generate a UK invitation letter")
    parser.add_argument("--data", type=pathlib.Path, help="Invitation data file path", required=True)
    parser.add_argument("--output", type=pathlib.Path, help="Output path for the invitation", required=True)

    args = parser.parse_args()
    build(args.data, args.output)


if __name__ == "__main__":
    main()
