import pytest


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
