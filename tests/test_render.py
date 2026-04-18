import pathlib
import re
import shutil
import subprocess

import pytest

from invitation.builder import build

REPO_ROOT = pathlib.Path(__file__).parent.parent
README = REPO_ROOT / "README.md"
FIXTURE_DIR = pathlib.Path(__file__).parent / "fixtures" / "render"
BASELINE_PDF = FIXTURE_DIR / "baseline.pdf"
ARTIFACT_DIR = REPO_ROOT / "tests" / "_artifacts" / "render"


def _readme_example_yaml() -> str:
    text = README.read_text(encoding="utf-8")
    blocks = re.findall(r"```yaml\n(.*?)\n```", text, re.DOTALL)
    if len(blocks) != 1:
        raise AssertionError(f"expected exactly one yaml block in README, found {len(blocks)}")
    return blocks[0]


@pytest.fixture
def example_data_file(tmp_path: pathlib.Path) -> pathlib.Path:
    data = tmp_path / "data.yml"
    data.write_text(_readme_example_yaml(), encoding="utf-8")
    return data


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
        f"rendered PDF differs from baseline\n"
        f"  artifacts: {ARTIFACT_DIR}\n"
        f"  diff-pdf stderr: {result.stderr.strip()}"
    )
