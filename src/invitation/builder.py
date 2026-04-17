import pathlib
import shutil
import subprocess
import tempfile
from typing import Final, Literal, get_args

import jinja2
from pydantic_yaml import parse_yaml_raw_as

from .model import InvitationConfig
from .util import date_format, fix_floating_punctuation, phone_format

Engine = Literal["xelatex", "lualatex"]
ENGINES: Final[tuple[Engine, ...]] = get_args(Engine)


def build(config_file: pathlib.Path, output_file: pathlib.Path, engine: Engine = "xelatex") -> None:
    config = parse_yaml_raw_as(InvitationConfig, config_file.read_text(encoding="utf-8"))

    template_env = jinja2.Environment(
        loader=jinja2.PackageLoader("invitation", "templates"),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template = template_env.get_template("invitation.tex.jinja")
    output_text = template.render(
        inviter=config.inviter,
        invitee=config.invitee,
        employer=config.employer,
        embassy=config.embassy,
        trip=config.trip,
        docs=config.docs,
        date_format=date_format,
        phone_format=phone_format,
    )
    output_text = fix_floating_punctuation(output_text)

    with tempfile.TemporaryDirectory() as temp_dir_name:
        temp_dir = pathlib.Path(temp_dir_name)
        tex_file = temp_dir / "invitation.tex"
        pdf_file = temp_dir / "invitation.pdf"

        tex_file.write_text(output_text, encoding="utf-8")
        subprocess.run(
            ["latexmk", f"-{engine}", f"-output-directory={temp_dir}", tex_file],
            check=True,
        )
        shutil.move(pdf_file, output_file)
