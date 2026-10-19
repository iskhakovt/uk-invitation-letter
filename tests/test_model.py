import datetime

import pytest
from pydantic import ValidationError

from invitation.model import THEY, Embassy, InvitationConfig, Invitee, Pronoun, Trip
from tests.data import INVITER, MINIMAL_DATA, TRIP


class TestAddressAndName:
    def test_lines_are_kept_as_given(self) -> None:
        embassy = Embassy.model_validate({"name": "E", "address": ["10 Downing Street", " London SW1A 2AA "]})
        assert embassy.address == ("10 Downing Street", "London SW1A 2AA")

    def test_empty_address_rejected(self) -> None:
        with pytest.raises(ValidationError, match="at least 1 item"):
            Embassy.model_validate({"name": "E", "address": []})

    def test_blank_address_line_rejected(self) -> None:
        with pytest.raises(ValidationError, match="at least 1 character"):
            Embassy.model_validate({"name": "E", "address": [" "]})

    def test_blank_name_rejected(self) -> None:
        with pytest.raises(ValidationError, match="at least 1 character"):
            Embassy.model_validate({"name": "   ", "address": ["x"]})


class TestInvitee:
    def test_single_name_shorthand(self) -> None:
        invitee = Invitee.model_validate({"name": "Alice Smith", "relationship": "friend"})
        assert invitee.name == ("Alice Smith",)
        assert invitee.pronoun == THEY

    def test_list_of_names(self) -> None:
        invitee = Invitee.model_validate({"name": ["Joseph Brodsky", "Maria Sozzani"], "relationship": "friends"})
        assert invitee.name == ("Joseph Brodsky", "Maria Sozzani")

    def test_single_person_uses_own_pronoun(self) -> None:
        invitee = Invitee.model_validate({"name": "Carol Lee", "pronoun": "she/her/her", "relationship": "mother"})
        assert invitee.pronoun.subject == "she"

    def test_group_may_state_the_default(self) -> None:
        invitee = Invitee.model_validate({"name": ["A", "B"], "pronoun": "they/them/their", "relationship": "x"})
        assert invitee.pronoun == THEY

    @pytest.mark.parametrize(
        ("data", "hint"),
        [
            ({"name": ["A", "B"], "pronoun": "she/her/her", "relationship": "x"}, "applies to a single invitee"),
            ({"name": "", "relationship": "x"}, r"name\.0\n  String should have at least 1 character"),
            ({"name": [], "relationship": "x"}, "at least one person"),
            ({"name": None, "relationship": "x"}, "string or a list of strings"),
            ({"relationship": "x"}, "name"),
        ],
    )
    def test_bad_input(self, data: dict[str, object], hint: str) -> None:
        with pytest.raises(ValidationError, match=hint):
            Invitee.model_validate(data)


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

    def test_null_in_a_data_file_means_default(self) -> None:
        data = {**MINIMAL_DATA, "invitee": {"name": "Bob", "relationship": "x", "pronoun": None}}
        assert InvitationConfig.model_validate(data).invitee.pronoun == THEY

    def test_mapping_with_unknown_key_rejected(self) -> None:
        with pytest.raises(ValidationError, match="typo"):
            Pronoun.model_validate({"subject": "she", "object": "her", "determiner": "her", "typo": "x"})


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
        invitee = Invitee.model_validate({"name": "  Alice Smith ", "relationship": "x"})
        assert invitee.name == ("Alice Smith",)

    def test_blank_name_parts_rejected(self) -> None:
        with pytest.raises(ValidationError):
            Invitee.model_validate({"name": [""], "relationship": "x"})

    def test_pronoun_parts_are_stripped(self) -> None:
        p = Pronoun.model_validate(" she / her / her ")
        assert (p.subject, p.object, p.determiner) == ("she", "her", "her")

    @pytest.mark.parametrize("value", ["//", "she//her", " / / ", ["she", "her", "her"], 42])
    def test_pronoun_bad_input_gets_the_format_hint(self, value: object) -> None:
        with pytest.raises(ValidationError, match="e.g. `she/her/her`") as info:
            Pronoun.model_validate(value)
        assert [error["loc"] for error in info.value.errors()] == [()]

    def test_blank_optional_text_rejected(self) -> None:
        data = {**MINIMAL_DATA, "trip": {**TRIP, "reason": ""}}
        with pytest.raises(ValidationError):
            InvitationConfig.model_validate(data)


class TestValidation:
    def test_departure_before_arrival_rejected(self) -> None:
        with pytest.raises(ValidationError, match="must not be before"):
            Trip(arrival_date=datetime.date(2026, 1, 31), departure_date=datetime.date(2026, 1, 1))

    def test_same_day_trip_allowed(self) -> None:
        Trip(arrival_date=datetime.date(2026, 1, 1), departure_date=datetime.date(2026, 1, 1))

    def test_invalid_phone_rejected(self) -> None:
        with pytest.raises(ValidationError, match="not a possible phone number"):
            InvitationConfig.model_validate({**MINIMAL_DATA, "inviter": {**INVITER, "phone": "0775"}})
