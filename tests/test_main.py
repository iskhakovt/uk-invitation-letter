import pathlib

import pytest

from invitation.builder import Engine
from invitation.main import ENGINE_ENV, main
from invitation.template import load_template_yaml


def test_gen_prints_template(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["gen"]) == 0
    assert capsys.readouterr().out == load_template_yaml()


def test_render_missing_data_file(tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]) -> None:
    missing = tmp_path / "nope.yml"
    assert main(["render", "--data", str(missing), "--output", str(tmp_path / "out.pdf")]) == 1
    err = capsys.readouterr().err
    assert err.startswith("error: ")
    assert "nope.yml" in err


def test_render_invalid_data_file(tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]) -> None:
    data = tmp_path / "data.yml"
    data.write_text("inviter: {}\n", encoding="utf-8")
    assert main(["render", "--data", str(data), "--output", str(tmp_path / "out.pdf")]) == 1
    err = capsys.readouterr().err
    assert "is not a valid data file" in err
    assert "invitee" in err


def test_render_malformed_yaml(tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]) -> None:
    data = tmp_path / "data.yml"
    data.write_text("inviter: [\n  bad: {\n", encoding="utf-8")
    assert main(["render", "--data", str(data), "--output", str(tmp_path / "out.pdf")]) == 1
    assert "is not valid YAML" in capsys.readouterr().err


def test_render_non_utf8_data_file(tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]) -> None:
    data = tmp_path / "data.yml"
    data.write_bytes(b"\xff\xfei\x00n\x00")
    assert main(["render", "--data", str(data), "--output", str(tmp_path / "out.pdf")]) == 1
    assert "is not UTF-8 encoded" in capsys.readouterr().err


def test_render_without_latexmk(
    example_data_file: pathlib.Path,
    tmp_path: pathlib.Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("invitation.builder.shutil.which", lambda _: None)
    assert main(["render", "--data", str(example_data_file), "--output", str(tmp_path / "out.pdf")]) == 1
    assert "latexmk not found" in capsys.readouterr().err


def test_unknown_command_exits_via_argparse() -> None:
    with pytest.raises(SystemExit):
        main(["bogus"])


@pytest.fixture
def built_engines(monkeypatch: pytest.MonkeyPatch) -> list[Engine]:
    """The engine of every `build` call, which is stubbed out."""
    engines: list[Engine] = []
    monkeypatch.setattr("invitation.main.build", lambda _data, _output, engine: engines.append(engine))
    return engines


def _render(tmp_path: pathlib.Path, *args: str) -> int:
    return main(["render", "--data", str(tmp_path / "data.yml"), "--output", str(tmp_path / "out.pdf"), *args])


@pytest.mark.parametrize(
    ("env", "args", "expected"),
    [
        (None, (), Engine.XELATEX),
        ("", (), Engine.XELATEX),
        ("tectonic", (), Engine.TECTONIC),
        ("tectonic", ("--engine", "lualatex"), Engine.LUALATEX),
    ],
    ids=["unset", "empty", "from-env", "flag-beats-env"],
)
def test_render_default_engine(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
    built_engines: list[Engine],
    env: str | None,
    args: tuple[str, ...],
    expected: Engine,
) -> None:
    if env is not None:
        monkeypatch.setenv(ENGINE_ENV, env)
    assert _render(tmp_path, *args) == 0
    assert built_engines == [expected]


def test_render_invalid_engine_env(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    built_engines: list[Engine],
) -> None:
    monkeypatch.setenv(ENGINE_ENV, "context")
    with pytest.raises(SystemExit) as excinfo:
        _render(tmp_path)
    assert excinfo.value.code == 2
    assert f"{ENGINE_ENV}: invalid choice: 'context'" in capsys.readouterr().err
    assert built_engines == []


def test_gen_ignores_engine_env(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setenv(ENGINE_ENV, "context")
    assert main(["gen"]) == 0
    assert capsys.readouterr().out == load_template_yaml()
