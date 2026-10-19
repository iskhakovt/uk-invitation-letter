import pathlib
import shutil
import subprocess
import tempfile
from collections.abc import Mapping
from typing import Final, Literal, get_args

import jinja2
from pydantic import ValidationError
from pydantic_yaml import parse_yaml_raw_as
from ruamel.yaml import YAMLError

from .filters import FILTERS
from .model import InvitationConfig
from .util import fix_floating_punctuation, tex_escape

Engine = Literal["xelatex", "lualatex", "pdflatex", "tectonic"]
ENGINES: Final[tuple[Engine, ...]] = get_args(Engine)

# Engines driven through latexmk, and the latexmk flag that selects each.
_LATEXMK_FLAG: Final[Mapping[Engine, str]] = {"xelatex": "-xelatex", "lualatex": "-lualatex", "pdflatex": "-pdf"}


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
if clash := FILTERS.keys() & _TEMPLATE_ENV.filters.keys():
    raise RuntimeError(f"filter names shadow Jinja built-ins: {sorted(clash)}")
_TEMPLATE_ENV.filters.update(FILTERS)


def _format_validation_error(e: ValidationError) -> str:
    lines = []
    for error in e.errors():
        location = ".".join(str(part) for part in error["loc"]) or "(top level)"
        lines.append(f"  {location}: {error['msg'].removeprefix('Value error, ')}")
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
    )
    return fix_floating_punctuation(output_text)


def _command(engine: Engine, tex_file: pathlib.Path, out_dir: pathlib.Path) -> list[str | pathlib.Path]:
    """The compiler invocation for `engine`, writing its outputs into `out_dir`."""
    if engine == "tectonic":
        # Tectonic is a self-contained XeTeX; it fetches packages itself and needs no latexmk.
        return ["tectonic", "--outdir", out_dir, tex_file]
    return [
        "latexmk",
        _LATEXMK_FLAG[engine],
        "-interaction=nonstopmode",
        "-halt-on-error",
        f"-output-directory={out_dir}",
        tex_file,
    ]


def _required_tools(engine: Engine) -> tuple[str, ...]:
    return ("tectonic",) if engine == "tectonic" else ("latexmk", engine)


def compile_pdf(tex_source: str, output_file: pathlib.Path, engine: Engine = "xelatex") -> None:
    """Compile LaTeX source with `engine` and move the resulting PDF to `output_file`."""
    tools = _required_tools(engine)
    for tool in tools:
        if shutil.which(tool) is None:
            raise BuildError(f"{tool} not found on PATH; install " + (" and ".join(tools) if len(tools) > 1 else tool))

    with tempfile.TemporaryDirectory() as temp_dir_name:
        temp_dir = pathlib.Path(temp_dir_name)
        tex_file = temp_dir / "invitation.tex"
        pdf_file = temp_dir / "invitation.pdf"

        tex_file.write_text(tex_source, encoding="utf-8")
        result = subprocess.run(_command(engine, tex_file, temp_dir))
        if result.returncode != 0:
            raise BuildError(f"{tools[0]} exited with status {result.returncode}; see the LaTeX output above")

        output_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(pdf_file, output_file)


def build(config_file: pathlib.Path, output_file: pathlib.Path, engine: Engine = "xelatex") -> None:
    compile_pdf(render_tex(load_config(config_file)), output_file, engine)
