"""Shared test data. Immutable by type: build variants with `{**MINIMAL_DATA, "trip": {...}}`."""

from collections.abc import Mapping
from typing import Final

# The smallest data file InvitationConfig accepts.
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
