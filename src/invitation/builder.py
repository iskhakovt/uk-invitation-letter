import pathlib
import shutil
import subprocess
import tempfile
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import Final

import jinja2
from pydantic import ValidationError
from pydantic_yaml import parse_yaml_raw_as
from ruamel.yaml import YAMLError

from .filters import FILTERS
from .model import InvitationConfig
from .util import fix_floating_punctuation, tex_escape


class Engine(StrEnum):
    XELATEX = "xelatex"
    LUALATEX = "lualatex"
    PDFLATEX = "pdflatex"
    TECTONIC = "tectonic"


Command = list[str | pathlib.Path]


def _latexmk(flag: str) -> Callable[[pathlib.Path, pathlib.Path], Command]:
    def command(tex_file: pathlib.Path, out_dir: pathlib.Path) -> Command:
        return ["latexmk", flag, "-interaction=nonstopmode", "-halt-on-error", f"-output-directory={out_dir}", tex_file]

    return command


def _tectonic(tex_file: pathlib.Path, out_dir: pathlib.Path) -> Command:
    # Tectonic is a self-contained XeTeX; it fetches packages itself and needs no latexmk.
    return ["tectonic", "--outdir", out_dir, tex_file]


@dataclass(frozen=True, slots=True)
class _Runner:
    tools: tuple[str, ...]  # binaries that must be on PATH
    command: Callable[[pathlib.Path, pathlib.Path], Command]  # (tex file, output dir) -> argv


_RUNNERS: Final[Mapping[Engine, _Runner]] = {
    Engine.XELATEX: _Runner(("latexmk", "xelatex"), _latexmk("-xelatex")),
    Engine.LUALATEX: _Runner(("latexmk", "lualatex"), _latexmk("-lualatex")),
    Engine.PDFLATEX: _Runner(("latexmk", "pdflatex"), _latexmk("-pdf")),
    Engine.TECTONIC: _Runner(("tectonic",), _tectonic),
}
assert _RUNNERS.keys() == set(Engine)


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


def required_tools(engine: Engine) -> tuple[str, ...]:
    """The binaries `engine` needs on PATH."""
    return _RUNNERS[engine].tools


def compile_pdf(tex_source: str, output_file: pathlib.Path, engine: Engine = Engine.XELATEX) -> None:
    """Compile LaTeX source with `engine` and move the resulting PDF to `output_file`."""
    runner = _RUNNERS[engine]
    for tool in runner.tools:
        if shutil.which(tool) is None:
            raise BuildError(f"{tool} not found on PATH; install " + " and ".join(runner.tools))

    with tempfile.TemporaryDirectory() as temp_dir_name:
        temp_dir = pathlib.Path(temp_dir_name)
        tex_file = temp_dir / "invitation.tex"
        pdf_file = temp_dir / "invitation.pdf"

        tex_file.write_text(tex_source, encoding="utf-8")
        result = subprocess.run(runner.command(tex_file, temp_dir))
        if result.returncode != 0:
            raise BuildError(f"{runner.tools[0]} exited with status {result.returncode}; see the LaTeX output above")

        output_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(pdf_file, output_file)


def build(config_file: pathlib.Path, output_file: pathlib.Path, engine: Engine = Engine.XELATEX) -> None:
    compile_pdf(render_tex(load_config(config_file)), output_file, engine)
