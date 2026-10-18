"""Shared test constants. The data is immutable by type: build variants with `{**MINIMAL_DATA, "trip": {...}}`."""

import pathlib
from collections.abc import Mapping
from typing import Final

REPO_ROOT: Final[pathlib.Path] = pathlib.Path(__file__).parent.parent
README: Final[pathlib.Path] = REPO_ROOT / "README.md"

INVITER: Final[Mapping[str, object]] = {
    "name": "Alice Smith",
    "address": ["1 Example Road", "EX1 2AB"],
    "phone": "07700900000",
    "email": "a@example.com",
}
TRIP: Final[Mapping[str, object]] = {"arrival_date": "2026-01-01", "departure_date": "2026-01-10"}

# The smallest data file InvitationConfig accepts.
MINIMAL_DATA: Final[Mapping[str, object]] = {
    "inviter": INVITER,
    "invitee": {"name": "Bob Jones", "relationship": "friend"},
    "embassy": {"name": "British Embassy", "address": ["Foreign City"]},
    "trip": TRIP,
}
