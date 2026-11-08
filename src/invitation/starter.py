from importlib import resources


def load_starter_yaml() -> str:
    """The starter data file that `gen` prints, for the user to fill in."""
    return resources.files("invitation").joinpath("starter.yml").read_text(encoding="utf-8")
