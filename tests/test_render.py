import pathlib
import shutil
import subprocess

import pytest

from invitation.builder import ENGINES, Engine, _required_tools, build
from tests.data import REPO_ROOT

FIXTURE_DIR: pathlib.Path = pathlib.Path(__file__).parent / "fixtures" / "render"
ARTIFACT_DIR: pathlib.Path = REPO_ROOT / "tests" / "_artifacts" / "render"


def _baseline(engine: Engine) -> pathlib.Path:
    return FIXTURE_DIR / f"baseline-{engine}.pdf"


@pytest.mark.render
@pytest.mark.parametrize("engine", ENGINES)
def test_render_matches_baseline(
    tmp_path: pathlib.Path,
    example_data_file: pathlib.Path,
    record_baselines: bool,
    require_engines: bool,
    monkeypatch: pytest.MonkeyPatch,
    engine: Engine,
) -> None:
    missing = [tool for tool in _required_tools(engine) if shutil.which(tool) is None]
    if missing:
        if require_engines:
            pytest.fail(f"{', '.join(missing)} not installed")
        pytest.skip(f"{', '.join(missing)} not installed")
    if not record_baselines:
        assert shutil.which("diff-pdf"), "diff-pdf not installed"

    monkeypatch.setenv("SOURCE_DATE_EPOCH", "0")
    monkeypatch.setenv("FORCE_SOURCE_DATE", "1")

    actual = tmp_path / "actual.pdf"
    build(example_data_file, actual, engine)

    baseline = _baseline(engine)
    if record_baselines:
        FIXTURE_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(actual, baseline)
        return

    if not baseline.exists():
        pytest.fail(f"no baseline at {baseline}; run pytest with --record-baselines to create one")

    artifacts = ARTIFACT_DIR / engine
    artifacts.mkdir(parents=True, exist_ok=True)
    diff_pdf = artifacts / "diff.pdf"
    if diff_pdf.exists():
        diff_pdf.unlink()

    result = subprocess.run(
        ["diff-pdf", "--mark-differences", f"--output-diff={diff_pdf}", str(baseline), str(actual)],
        capture_output=True,
        text=True,
    )

    if result.returncode == 0:
        return

    shutil.copyfile(actual, artifacts / "actual.pdf")
    shutil.copyfile(baseline, artifacts / "expected.pdf")
    pytest.fail(
        f"{engine}: rendered PDF differs from baseline\n"
        f"  artifacts: {artifacts}\n"
        f"  diff-pdf stderr: {result.stderr.strip()}"
    )
