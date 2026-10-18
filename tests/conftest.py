import pathlib
import re
from collections.abc import Mapping
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


# The smallest data file InvitationConfig accepts. It is immutable by type, so
# tests build variants with `{**minimal_data, "trip": {...}}` rather than
# editing it in place; the fixture exists because test modules cannot import
# from conftest under pytest's importlib mode.
MINIMAL_DATA: Final[Mapping[str, object]] = {
    "inviter": {
        "name": "Alice Smith",
        "address": ["1 Example Road", "EX1 2AB"],
        "phone": "07700900000",
        "email": "a@example.com",
    },
    "invitee": {"name": "Bob Jones", "relationship": "friend"},
    "embassy": {"name": "British Embassy", "address": ["Foreign City"]},
    "trip": {"arrival_date": "2026-01-01", "departure_date": "2026-01-10"},
}


@pytest.fixture
def minimal_data() -> Mapping[str, object]:
    return MINIMAL_DATA


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
