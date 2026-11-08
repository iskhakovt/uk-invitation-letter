from pydantic_yaml import parse_yaml_raw_as

from invitation.model import InvitationConfig
from invitation.starter import load_starter_yaml


def test_load_starter_yaml_returns_non_empty_text() -> None:
    text = load_starter_yaml()
    assert text.strip()
    assert "inviter:" in text


def test_starter_yaml_is_valid_invitation_config() -> None:
    text = load_starter_yaml()
    parse_yaml_raw_as(InvitationConfig, text)
