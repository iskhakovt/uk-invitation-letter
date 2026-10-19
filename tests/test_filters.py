import datetime

from invitation.builder import _TEMPLATE_ENV
from invitation.filters import FILTERS, address_block, address_inline, first_names, names, nobreak
from invitation.util import Tex


class TestNames:
    def test_single(self) -> None:
        assert names(("Alice Smith",)) == "Alice~Smith"
        assert first_names(("Alice Smith",)) == "Alice"

    def test_two_joined_with_and(self) -> None:
        assert names(("Joseph Brodsky", "Maria Sozzani")) == "Joseph~Brodsky and Maria~Sozzani"
        assert first_names(("Joseph Brodsky", "Maria Sozzani")) == "Joseph and Maria"

    def test_three_use_oxford_comma(self) -> None:
        assert names(("Alice Smith", "Bob Jones", "Carol Lee")) == "Alice~Smith, Bob~Jones, and~Carol~Lee"

    def test_typed_tilde_keeps_first_name_together(self) -> None:
        assert first_names(("Mary~Ann Smith",)) == "Mary~Ann"

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


class TestRegistration:
    def test_every_filter_is_registered_and_returns_tex(self) -> None:
        for name, fn in FILTERS.items():
            assert _TEMPLATE_ENV.filters[name] is fn
        assert isinstance(nobreak("x y"), Tex)
        assert isinstance(FILTERS["date"](datetime.date(2026, 1, 5)), Tex)
        assert isinstance(FILTERS["phone"]("07758888305"), Tex)
