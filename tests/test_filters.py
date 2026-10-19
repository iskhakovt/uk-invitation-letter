import datetime

import pytest

from invitation.filters import FILTERS, address_block, address_inline, date, first_names, names, phone
from invitation.util import Tex, tex_nobreak


class TestNames:
    def test_single(self) -> None:
        assert names(("Alice Smith",)) == "Alice~Smith"
        assert first_names(("Alice Smith",)) == "Alice"

    def test_two_joined_with_and(self) -> None:
        assert names(("Joseph Brodsky", "Maria Sozzani")) == "Joseph~Brodsky and Maria~Sozzani"
        assert first_names(("Joseph Brodsky", "Maria Sozzani")) == "Joseph and Maria"

    def test_three_use_oxford_comma_and_nbsp(self) -> None:
        assert names(("Alice Smith", "Bob Jones", "Carol Lee")) == "Alice~Smith, Bob~Jones, and~Carol~Lee"
        assert first_names(("A B", "C D", "E F", "G H")) == "A, C, E, and~G"

    def test_typed_tilde_keeps_first_name_together(self) -> None:
        assert first_names(("Mary~Ann Smith",)) == "Mary~Ann"

    @pytest.mark.parametrize("space", ["\t", "\u00a0", "  "])
    def test_first_name_ends_at_any_whitespace(self, space: str) -> None:
        assert first_names((f"Alice{space}Smith",)) == "Alice"

    def test_name_that_split_discards_is_used_whole(self) -> None:
        # U+001C is not Unicode White_Space (so pydantic keeps it) but str.split() drops it.
        assert first_names(("\x1c",)) == "\x1c"

    def test_escaped(self) -> None:
        assert names(("Marks & Spencer", "Bob_Jones")) == "Marks~\\&~Spencer and Bob\\_Jones"
        assert first_names(("Marks & Spencer", "Bob_Jones")) == "Marks and Bob\\_Jones"


class TestAddress:
    def test_inline_joins_with_comma(self) -> None:
        assert address_inline(("10 Downing Street", "London SW1A 2AA")) == "10~Downing~Street, London~SW1A~2AA"

    def test_block_uses_latex_break(self) -> None:
        assert address_block(("1 Example Road", "City")) == "1~Example~Road\\\\\nCity"

    def test_escaped(self) -> None:
        assert address_inline(("Flat #3", "100% Street")) == "Flat~\\#3, 100\\%~Street"
        assert address_block(("Flat #3", "100% Street")) == "Flat~\\#3\\\\\n100\\%~Street"


class TestDate:
    def test_single_digit_day_has_no_leading_zero(self) -> None:
        assert date(datetime.date(2026, 1, 5)) == "5~January~2026"

    def test_two_digit_day(self) -> None:
        assert date(datetime.date(2026, 12, 25)) == "25~December~2026"


class TestPhone:
    def test_uk_mobile(self) -> None:
        assert phone("07758888305") == "07758~888305"

    def test_with_country_code(self) -> None:
        assert phone("+447758888305") == "07758~888305"

    def test_rejects_garbage(self) -> None:
        with pytest.raises(ValueError):
            phone("call me")


SAMPLE_CALLS: dict[str, tuple[object, ...]] = {
    "nobreak": ("a b",),
    "names": (("A B", "C D"),),
    "first_names": (("A B", "C D"),),
    "address_inline": (("1 Road", "Town"),),
    "address_block": (("1 Road", "Town"),),
    "date": (datetime.date(2026, 1, 5),),
    "phone": ("07758888305",),
}


class TestSequenceFiltersRejectAString:
    @pytest.mark.parametrize("name", ["names", "first_names", "address_inline", "address_block"])
    def test_bare_string_raises(self, name: str) -> None:
        with pytest.raises(TypeError, match="use the `nobreak` filter"):
            FILTERS[name]("Alice Smith")


class TestEveryFilter:
    def test_table_and_samples_cover_the_same_filters(self) -> None:
        assert SAMPLE_CALLS.keys() == FILTERS.keys()
        assert FILTERS["nobreak"] is tex_nobreak

    @pytest.mark.parametrize("name", sorted(SAMPLE_CALLS))
    def test_returns_tex(self, name: str) -> None:
        assert isinstance(FILTERS[name](*SAMPLE_CALLS[name]), Tex)
