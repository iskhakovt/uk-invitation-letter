from pydantic_yaml import parse_yaml_raw_as

from invitation.model import InvitationConfig
from invitation.template import load_template_yaml


def test_load_template_yaml_returns_non_empty_text() -> None:
    text = load_template_yaml()
    assert text.strip()
    assert "inviter:" in text


def test_template_yaml_is_valid_invitation_config() -> None:
    text = load_template_yaml()
    parse_yaml_raw_as(InvitationConfig, text)
