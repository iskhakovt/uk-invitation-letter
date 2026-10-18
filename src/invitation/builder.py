import pathlib
import shutil
import subprocess
import tempfile
from typing import Final, Literal, get_args

import jinja2
from pydantic import ValidationError
from pydantic_yaml import parse_yaml_raw_as
from ruamel.yaml import YAMLError

from .model import InvitationConfig
from .util import date_format, fix_floating_punctuation, phone_format, tex_escape

Engine = Literal["xelatex", "lualatex"]
ENGINES: Final[tuple[Engine, ...]] = get_args(Engine)


class BuildError(Exception):
    """The letter could not be produced; the message is suitable for showing to the user."""


def _finalize(value: object) -> object:
    # Every `{{ ... }}` expression passes through here. Strings are user text
    # and get escaped; `tex_escape` itself passes `Tex` values through.
    return tex_escape(value) if isinstance(value, str) else value


_TEMPLATE_ENV: Final[jinja2.Environment] = jinja2.Environment(
    loader=jinja2.PackageLoader("invitation", "templates"),
    trim_blocks=True,
    lstrip_blocks=True,
    finalize=_finalize,
)


def _format_validation_error(e: ValidationError) -> str:
    lines = []
    for error in e.errors():
        location = ".".join(str(part) for part in error["loc"]) or "(top level)"
        lines.append(f"  {location}: {error['msg']}")
    return "\n".join(lines)


def load_config(config_file: pathlib.Path) -> InvitationConfig:
    """Read and validate a data file. Raises BuildError for anything other than an unreadable file."""
    try:
        text = config_file.read_text(encoding="utf-8")
    except UnicodeDecodeError as e:
        raise BuildError(f"{config_file} is not UTF-8 encoded: {e}") from e
    try:
        return parse_yaml_raw_as(InvitationConfig, text)
    except YAMLError as e:
        raise BuildError(f"{config_file} is not valid YAML:\n{e}") from e
    except ValidationError as e:
        raise BuildError(f"{config_file} is not a valid data file:\n{_format_validation_error(e)}") from e


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
    for tool in ("latexmk", engine):
        if shutil.which(tool) is None:
            raise BuildError(f"{tool} not found on PATH; install a TeX distribution that provides latexmk and {engine}")

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
