import pathlib
import subprocess

import jinja2
from pydantic_yaml import parse_yaml_raw_as

from .model import InvitationConfig
from .util import date_format, fix_floating_punctuation, phone_format


def main() -> None:
    with open("data.yml") as config_file:
        config = parse_yaml_raw_as(InvitationConfig, config_file.read())

    template_env = jinja2.Environment(loader=jinja2.PackageLoader("invitation", "templates"))
    template = template_env.get_template("invitation.tex.jinja")
    output_text = template.render(
        inviter=config.inviter,
        invitee=config.invitee,
        employer=config.employer,
        embassy=config.embassy,
        trip=config.trip,
        date_format=date_format,
        phone_format=phone_format,
    )
    output_text = fix_floating_punctuation(output_text)

    pathlib.Path("build").mkdir(exist_ok=True)

    with open("build/invitation.tex", "w") as output_file:
        output_file.write(output_text)

    subprocess.call(["latexmk", "-pdf", "-output-directory=build", "build/invitation.tex"])


if __name__ == "__main__":
    main()
