import datetime

import pytest

from invitation.util import (
    Tex,
    and_join,
    date_format,
    fix_floating_punctuation,
    parse_phone,
    phone_format,
    tex_escape,
    tex_nobreak,
    use_non_breaking_space,
)


class TestAndJoin:
    def test_empty(self) -> None:
        assert and_join([]) == ""

    def test_single(self) -> None:
        assert and_join(["Alice"]) == "Alice"

    def test_two(self) -> None:
        assert and_join(["Alice", "Bob"]) == "Alice and Bob"

    def test_three_uses_oxford_comma_and_nbsp(self) -> None:
        assert and_join(["Alice", "Bob", "Carol"]) == "Alice, Bob, and~Carol"

    def test_four(self) -> None:
        assert and_join(["A", "B", "C", "D"]) == "A, B, C, and~D"


class TestUseNonBreakingSpace:
    def test_replaces_spaces(self) -> None:
        assert use_non_breaking_space("John H Smith") == "John~H~Smith"

    def test_no_spaces(self) -> None:
        assert use_non_breaking_space("Alice") == "Alice"

    def test_empty(self) -> None:
        assert use_non_breaking_space("") == ""


class TestDateFormat:
    def test_single_digit_day_has_no_leading_zero(self) -> None:
        assert date_format(datetime.date(2026, 1, 5)) == "5~January~2026"

    def test_two_digit_day(self) -> None:
        assert date_format(datetime.date(2026, 12, 25)) == "25~December~2026"


class TestPhoneFormat:
    def test_uk_mobile(self) -> None:
        assert phone_format("07758888305") == "07758~888305"

    def test_with_country_code(self) -> None:
        assert phone_format("+447758888305") == "07758~888305"


class TestFixFloatingPunctuation:
    def test_removes_space_before_comma(self) -> None:
        assert fix_floating_punctuation("hello , world") == "hello, world"

    @pytest.mark.parametrize("punct", [",", ".", ";", ":", "!", "?"])
    def test_all_punctuation(self, punct: str) -> None:
        assert fix_floating_punctuation(f"word {punct}") == f"word{punct}"

    def test_leaves_normal_text_alone(self) -> None:
        assert fix_floating_punctuation("a simple sentence.") == "a simple sentence."

    def test_collapses_multiple_spaces_before_punct(self) -> None:
        assert fix_floating_punctuation("word   ,") == "word,"


class TestTexEscape:
    def test_escapes_all_specials(self) -> None:
        assert tex_escape(r"a&b%c$d#e_f{g}h^i\j") == r"a\&b\%c\$d\#e\_f\{g\}h\textasciicircum{}i\textbackslash{}j"

    def test_backslash_is_not_double_escaped(self) -> None:
        assert tex_escape("\\&") == r"\textbackslash{}\&"

    def test_escapes_tilde(self) -> None:
        assert tex_escape("~2 weeks") == r"\textasciitilde{}2 weeks"

    def test_returns_tex_and_is_idempotent_on_tex(self) -> None:
        once = tex_escape("50%")
        assert isinstance(once, Tex)
        assert tex_escape(once) == once == r"50\%"


class TestTexNobreak:
    def test_spaces_become_non_breaking_and_specials_are_escaped(self) -> None:
        assert tex_nobreak("Marks & Spencer plc") == r"Marks~\&~Spencer~plc"

    def test_typed_tilde_is_kept(self) -> None:
        assert tex_nobreak("Mary~Ann Smith") == "Mary~Ann~Smith"

    def test_returns_tex_and_is_idempotent_on_tex(self) -> None:
        once = tex_nobreak("a & b")
        assert isinstance(once, Tex)
        assert tex_nobreak(once) == once == r"a~\&~b"
        assert tex_nobreak(tex_escape("a&b")) == r"a\&b"


class TestParsePhone:
    def test_invalid_number(self) -> None:
        with pytest.raises(ValueError, match="not a possible phone number"):
            parse_phone("0775")

    def test_not_a_number(self) -> None:
        with pytest.raises(ValueError, match="not a phone number"):
            parse_phone("call me")

    def test_phone_format_rejects_garbage(self) -> None:
        with pytest.raises(ValueError):
            phone_format("call me")
