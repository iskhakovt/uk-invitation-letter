import pathlib
import shutil
import subprocess
import tempfile

import jinja2
from pydantic_yaml import parse_yaml_raw_as

from .model import InvitationConfig
from .util import date_format, fix_floating_punctuation, phone_format


def build(config_file: pathlib.Path, output_file: pathlib.Path) -> None:
    config = parse_yaml_raw_as(InvitationConfig, config_file.read_text())

    template_env = jinja2.Environment(loader=jinja2.PackageLoader("invitation", "templates"))
    template = template_env.get_template("invitation.tex.jinja")
    output_text = template.render(
        **config.__dict__,
        date_format=date_format,
        phone_format=phone_format,
    )
    output_text = fix_floating_punctuation(output_text)

    temp_dir = pathlib.Path(tempfile.mkdtemp())
    tex_file = temp_dir / "invitation.tex"
    pdf_file = temp_dir / "invitation.pdf"

    tex_file.write_text(output_text)
    subprocess.call(["latexmk", "-pdf", f"-output-directory={temp_dir.absolute()}", tex_file.absolute()])

    shutil.move(pdf_file, output_file)
