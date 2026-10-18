import pathlib
import shutil
import subprocess
import tempfile
from typing import Final, Literal, get_args

import jinja2
from pydantic_yaml import parse_yaml_raw_as

from .model import InvitationConfig
from .util import Tex, date_format, fix_floating_punctuation, phone_format, tex_escape

Engine = Literal["xelatex", "lualatex"]
ENGINES: Final[tuple[Engine, ...]] = get_args(Engine)


class BuildError(Exception):
    """The PDF could not be produced; the message is suitable for showing to the user."""


def _finalize(value: object) -> object:
    # Every `{{ ... }}` expression passes through here. Plain strings are user
    # text and get escaped; `Tex` values are already LaTeX and pass through.
    if isinstance(value, str) and not isinstance(value, Tex):
        return tex_escape(value)
    return value


_TEMPLATE_ENV = jinja2.Environment(
    loader=jinja2.PackageLoader("invitation", "templates"),
    trim_blocks=True,
    lstrip_blocks=True,
    finalize=_finalize,
)


def load_config(config_file: pathlib.Path) -> InvitationConfig:
    return parse_yaml_raw_as(InvitationConfig, config_file.read_text(encoding="utf-8"))


def render_tex(config: InvitationConfig) -> str:
    """Render the LaTeX source for the letter. Needs no TeX installation."""
    template = _TEMPLATE_ENV.get_template("invitation.tex.jinja")
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
    return fix_floating_punctuation(output_text)


def compile_pdf(tex_source: str, output_file: pathlib.Path, engine: Engine = "xelatex") -> None:
    """Compile LaTeX source with latexmk and move the resulting PDF to `output_file`."""
    if shutil.which("latexmk") is None:
        raise BuildError(f"latexmk not found on PATH; install a TeX distribution that provides latexmk and {engine}")

    with tempfile.TemporaryDirectory() as temp_dir_name:
        temp_dir = pathlib.Path(temp_dir_name)
        tex_file = temp_dir / "invitation.tex"
        pdf_file = temp_dir / "invitation.pdf"

        tex_file.write_text(tex_source, encoding="utf-8")
        result = subprocess.run(
            [
                "latexmk",
                f"-{engine}",
                "-interaction=nonstopmode",
                "-halt-on-error",
                f"-output-directory={temp_dir}",
                tex_file,
            ],
        )
        if result.returncode != 0:
            raise BuildError(f"latexmk exited with status {result.returncode}; see the LaTeX output above")

        output_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(pdf_file, output_file)


def build(config_file: pathlib.Path, output_file: pathlib.Path, engine: Engine = "xelatex") -> None:
    compile_pdf(render_tex(load_config(config_file)), output_file, engine)
