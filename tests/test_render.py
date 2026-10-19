import pathlib
import shutil
import subprocess
from typing import Final

import pytest

from invitation.builder import build
from tests.data import REPO_ROOT

FIXTURE_DIR: Final[pathlib.Path] = pathlib.Path(__file__).parent / "fixtures" / "render"
BASELINE_PDF: Final[pathlib.Path] = FIXTURE_DIR / "baseline.pdf"
ARTIFACT_DIR: Final[pathlib.Path] = REPO_ROOT / "tests" / "_artifacts" / "render"


@pytest.mark.render
def test_render_matches_baseline(
    tmp_path: pathlib.Path,
    example_data_file: pathlib.Path,
    record_baselines: bool,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert shutil.which("latexmk"), "latexmk not installed"
    assert shutil.which("xelatex"), "xelatex not installed"
    if not record_baselines:
        assert shutil.which("diff-pdf"), "diff-pdf not installed"

    monkeypatch.setenv("SOURCE_DATE_EPOCH", "0")
    monkeypatch.setenv("FORCE_SOURCE_DATE", "1")

    actual = tmp_path / "actual.pdf"
    build(example_data_file, actual)

    if record_baselines:
        FIXTURE_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(actual, BASELINE_PDF)
        return

    if not BASELINE_PDF.exists():
        pytest.fail(f"no baseline at {BASELINE_PDF}; run pytest with --record-baselines to create one")

    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    diff_pdf = ARTIFACT_DIR / "diff.pdf"
    if diff_pdf.exists():
        diff_pdf.unlink()

    result = subprocess.run(
        ["diff-pdf", "--mark-differences", f"--output-diff={diff_pdf}", str(BASELINE_PDF), str(actual)],
        capture_output=True,
        text=True,
    )

    if result.returncode == 0:
        return

    shutil.copyfile(actual, ARTIFACT_DIR / "actual.pdf")
    shutil.copyfile(BASELINE_PDF, ARTIFACT_DIR / "expected.pdf")
    pytest.fail(
        f"rendered PDF differs from baseline\n  artifacts: {ARTIFACT_DIR}\n  diff-pdf stderr: {result.stderr.strip()}"
    )
