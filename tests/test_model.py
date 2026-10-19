import datetime

import pytest
from pydantic import ValidationError

from invitation.model import THEY, Address, InvitationConfig, Name, Pronoun, Trip
from tests.data import INVITER, MINIMAL_DATA, TRIP


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
        assert (THEY.subject, THEY.object, THEY.determiner) == ("they", "them", "their")

    def test_slash_form(self) -> None:
        p = Pronoun.model_validate("she/her/her")
        assert p == Pronoun(subject="she", object="her", determiner="her")

    def test_null_means_default(self) -> None:
        assert Pronoun.model_validate(None) == THEY

    def test_must_have_three_parts(self) -> None:
        with pytest.raises(ValidationError, match="e.g. `she/her/her`"):
            Pronoun.model_validate("she/her")
        with pytest.raises(ValidationError, match="e.g. `she/her/her`"):
            Pronoun.model_validate("she/her/her/hers")


class TestInvitationConfig:
    def test_minimal_config_parses(self) -> None:
        cfg = InvitationConfig.model_validate(MINIMAL_DATA)
        assert cfg.employer is None
        assert cfg.docs == ()
        assert cfg.trip.financial_support is False
        assert cfg.trip.arrival_date == datetime.date(2026, 1, 1)

    def test_missing_required_field(self) -> None:
        data = {key: value for key, value in MINIMAL_DATA.items() if key != "embassy"}
        with pytest.raises(ValidationError):
            InvitationConfig.model_validate(data)


class TestWhitespaceAndBlanks:
    def test_name_is_stripped(self) -> None:
        assert Name("  Alice Smith ").short_name() == "Alice"

    def test_blank_name_parts_rejected(self) -> None:
        with pytest.raises(ValidationError):
            Name([""])
        with pytest.raises(ValidationError):
            Name("   ")

    def test_blank_address_line_rejected(self) -> None:
        with pytest.raises(ValidationError):
            Address([" "])

    def test_pronoun_parts_are_stripped(self) -> None:
        p = Pronoun.model_validate(" she / her / her ")
        assert (p.subject, p.object, p.determiner) == ("she", "her", "her")

    @pytest.mark.parametrize("value", ["//", "she//her", " / / "])
    def test_pronoun_blank_part_rejected(self, value: str) -> None:
        with pytest.raises(ValidationError, match="at least 1 character"):
            Pronoun.model_validate(value)

    @pytest.mark.parametrize("value", [["she", "her", "her"], 42])
    def test_pronoun_wrong_type_rejected(self, value: object) -> None:
        with pytest.raises(ValidationError):
            Pronoun.model_validate(value)

    def test_name_none_gets_a_hint(self) -> None:
        with pytest.raises(ValidationError, match="string or a list of strings"):
            Name(None)

    def test_blank_optional_text_rejected(self) -> None:
        data = {**MINIMAL_DATA, "trip": {**TRIP, "reason": ""}}
        with pytest.raises(ValidationError):
            InvitationConfig.model_validate(data)


class TestEscaping:
    def test_name_methods_escape(self) -> None:
        name = Name(["Marks & Spencer", "Bob_Jones"])
        assert name.full_name() == "Marks~\\&~Spencer and Bob\\_Jones"
        assert name.short_name() == "Marks and Bob\\_Jones"

    def test_address_methods_escape(self) -> None:
        addr = Address(["Flat #3", "100% Street"])
        assert addr.line() == "Flat~\\#3, 100\\%~Street"
        assert addr.multiline() == "Flat~\\#3\\\\\n100\\%~Street"


class TestValidation:
    def test_departure_before_arrival_rejected(self) -> None:
        with pytest.raises(ValidationError, match="must not be before"):
            Trip(arrival_date=datetime.date(2026, 1, 31), departure_date=datetime.date(2026, 1, 1))

    def test_same_day_trip_allowed(self) -> None:
        Trip(arrival_date=datetime.date(2026, 1, 1), departure_date=datetime.date(2026, 1, 1))

    def test_invalid_phone_rejected(self) -> None:
        with pytest.raises(ValidationError, match="not a possible phone number"):
            InvitationConfig.model_validate({**MINIMAL_DATA, "inviter": {**INVITER, "phone": "0775"}})
