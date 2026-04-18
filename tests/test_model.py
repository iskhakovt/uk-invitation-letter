import datetime
from typing import Any

import pytest
from pydantic import ValidationError

from invitation.model import Address, InvitationConfig, Name, Pronoun


class TestAddress:
    def test_line_joins_with_comma(self) -> None:
        addr = Address(["10 Downing Street", "London SW1A 2AA"])
        assert addr.line() == "10~Downing~Street, London~SW1A~2AA"

    def test_multiline_uses_latex_break(self) -> None:
        addr = Address(["1 Example Road", "City"])
        assert addr.multiline() == "1~Example~Road\\\\\nCity"

    def test_empty_rejected(self) -> None:
        with pytest.raises(ValidationError):
            Address([])


class TestName:
    def test_single_string(self) -> None:
        name = Name("Alice Smith")
        assert name.full_name() == "Alice~Smith"
        assert name.short_name() == "Alice"

    def test_list_of_names(self) -> None:
        name = Name(["Joseph Brodsky", "Maria Sozzani"])
        assert name.full_name() == "Joseph~Brodsky and Maria~Sozzani"
        assert name.short_name() == "Joseph and Maria"

    def test_three_names_oxford_comma(self) -> None:
        name = Name(["Alice Smith", "Bob Jones", "Carol Lee"])
        assert name.full_name() == "Alice~Smith, Bob~Jones, and~Carol~Lee"

    def test_empty_rejected(self) -> None:
        with pytest.raises(ValidationError):
            Name("")
        with pytest.raises(ValidationError):
            Name([])


class TestPronoun:
    def test_default_they_them_their(self) -> None:
        p = Pronoun()
        assert (p.subject, p.object, p.determiner) == ("they", "them", "their")

    def test_custom(self) -> None:
        p = Pronoun("she/her/her")
        assert (p.subject, p.object, p.determiner) == ("she", "her", "her")

    def test_must_have_three_parts(self) -> None:
        with pytest.raises(ValidationError):
            Pronoun("she/her")
        with pytest.raises(ValidationError):
            Pronoun("she/her/her/hers")


class TestInvitationConfig:
    def _minimal(self) -> dict[str, Any]:
        return {
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

    def test_minimal_config_parses(self) -> None:
        cfg = InvitationConfig(**self._minimal())
        assert cfg.employer is None
        assert cfg.docs == ()
        assert cfg.trip.financial_support is False
        assert cfg.trip.arrival_date == datetime.date(2026, 1, 1)

    def test_missing_required_field(self) -> None:
        data = self._minimal()
        del data["embassy"]
        with pytest.raises(ValidationError):
            InvitationConfig(**data)
