import datetime

import pytest

from invitation.util import (
    and_join,
    date_format,
    fix_floating_punctuation,
    phone_format,
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
