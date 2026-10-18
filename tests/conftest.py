import pathlib
import re
from typing import Final

import pytest

REPO_ROOT: Final[pathlib.Path] = pathlib.Path(__file__).parent.parent
README: Final[pathlib.Path] = REPO_ROOT / "README.md"


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--record-baselines",
        action="store_true",
        default=False,
        help="Record baseline outputs for render tests instead of comparing against them",
    )


@pytest.fixture
def record_baselines(request: pytest.FixtureRequest) -> bool:
    return request.config.getoption("--record-baselines")


@pytest.fixture(scope="session")
def readme_example_yaml() -> str:
    text = README.read_text(encoding="utf-8")
    blocks = re.findall(r"```yaml\n(.*?)\n```", text, re.DOTALL)
    assert len(blocks) == 1, f"expected exactly one yaml block in README, found {len(blocks)}"
    return blocks[0]


@pytest.fixture
def example_data_file(tmp_path: pathlib.Path, readme_example_yaml: str) -> pathlib.Path:
    data = tmp_path / "data.yml"
    data.write_text(readme_example_yaml, encoding="utf-8")
    return data
