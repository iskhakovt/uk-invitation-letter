import pathlib
import re
from typing import Any

import pytest
from pydantic_yaml import parse_yaml_raw_as

from invitation.builder import BuildError, compile_pdf, load_config, render_tex
from invitation.model import InvitationConfig

RAW_SPECIALS = re.compile(r"(?<!\\)[&%#_$]")  # an unescaped LaTeX special in rendered body text


def minimal(**overrides: Any) -> dict[str, Any]:
    data: dict[str, Any] = {
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
    data.update(overrides)
    return data


def render(**overrides: Any) -> str:
    return render_tex(InvitationConfig(**minimal(**overrides)))


class TestReadmeExample:
    def test_renders_expected_sentences(self, readme_example_yaml: str) -> None:
        tex = render_tex(parse_yaml_raw_as(InvitationConfig, readme_example_yaml))
        assert "my friends, Joseph~Brodsky and Maria~Sozzani, will apply for a UK visitor visa" in tex
        assert "from 1~January~2026 until 31~January~2026 for a short trip." in tex
        assert "I am able to accommodate Joseph and Maria at my place, 75~Hertingfordbury~Road, Newton~NG13~8QY." in tex
        assert "They will use their savings for the trip, and I will assist them" in tex
        assert "Joseph and Maria will return to the US to circumnavigate the globe." in tex
        assert "I am currently employed at Jstory~UK~Ltd, 89~Well~Lane, Patterdale~CA11~0LQ." in tex
        assert "\\item immigration status share code" in tex
        assert "\\item employment reference" in tex
        assert "\\item proof of address: council tax bill" in tex
        assert "\\item table tennis match result sheet" in tex
        assert "07758~888305" in tex

    def test_load_config_reads_yaml_file(self, example_data_file: pathlib.Path) -> None:
        assert load_config(example_data_file).inviter.email == "noreply@temporary-mail.net"


class TestEscaping:
    def test_specials_in_every_user_field_are_escaped(self) -> None:
        tex = render(
            inviter={
                "name": "Alice & Bob_Smith",
                "address": ["Flat #3, 75% Road", "EX1 2AB"],
                "phone": "07700900000",
                "email": "alice_smith@example.com",
                "residence": "visa {stamp}",
                "proof_of_address": "bill $",
            },
            invitee={"name": ["Bob ^ Jones"], "relationship": "friend & colleague"},
            employer={"name": "Marks & Spencer plc", "address": ["Baker St_1"]},
            embassy={"name": "Embassy #1", "address": ["1 Road \\ 2"]},
            trip={
                "arrival_date": "2026-01-01",
                "departure_date": "2026-01-10",
                "reason": "100% leisure",
                "return_reason": "to work at A&B",
                "return_country": "the US_A",
            },
            docs=["bank statement #2"],
        )
        body = tex.split("\\begin{document}", 1)[1]
        assert not RAW_SPECIALS.search(body), body
        assert "Alice~\\&~Bob\\_Smith" in tex
        assert "alice\\_smith@example.com" in tex
        assert "for 100\\% leisure." in tex
        assert "Flat~\\#3,~75\\%~Road" in tex
        assert "\\item visa \\{stamp\\}" in tex
        assert "Bob~\\textasciicircum{}~Jones" in tex
        assert "1~Road~\\textbackslash{}~2" in tex

    def test_tilde_is_preserved_as_non_breaking_space(self) -> None:
        tex = render(invitee={"name": "Mary~Ann Smith", "relationship": "sister"})
        assert "my sister, Mary~Ann~Smith," in tex
        assert "accommodate Mary~Ann at my place" in tex

    def test_address_multiline_break_survives_escaping(self) -> None:
        tex = render()
        assert "1~Example~Road\\\\\nEX1~2AB" in tex


class TestBranches:
    def test_no_employer_no_optionals(self) -> None:
        tex = render()
        assert "employed at" not in tex
        assert "employment reference" not in tex
        assert "After their trip" not in tex
        assert "proof of address" not in tex
        assert "until 10~January~2026.\n" in tex

    def test_financial_support(self) -> None:
        tex = render(trip={"arrival_date": "2026-01-01", "departure_date": "2026-01-10", "financial_support": True})
        assert (
            "will be in receipt of a return ticket and all of the expenses for their journey will be met by me." in tex
        )
        assert "\\item latest payslip" in tex
        assert "savings" not in tex

    @pytest.mark.parametrize(
        ("residence", "item"),
        [
            ("permit", "residence permit"),
            ("share code", "immigration status share code"),
            ("passport", "passport"),
            ("settled status letter", "settled status letter"),
        ],
    )
    def test_residence_variants(self, residence: str, item: str) -> None:
        inviter = minimal()["inviter"] | {"residence": residence}
        assert f"\\item {item}\n" in render(inviter=inviter)

    def test_return_country_only(self) -> None:
        tex = render(trip={"arrival_date": "2026-01-01", "departure_date": "2026-01-10", "return_country": "France"})
        assert "After their trip to the UK, Bob will return to France." in tex

    def test_return_reason_only(self) -> None:
        tex = render(trip={"arrival_date": "2026-01-01", "departure_date": "2026-01-10", "return_reason": "to study"})
        assert "After their trip to the UK, Bob will leave the UK to study." in tex

    def test_custom_pronouns(self) -> None:
        tex = render(invitee={"name": "Carol Lee", "relationship": "mother", "pronoun": "she/her/her"})
        assert "She will travel to the United~Kingdom" in tex
        assert "She will use her savings for the trip, and I will assist her" in tex
        assert "While in the UK, she will not engage" in tex


class TestCompilePdf:
    def test_missing_latexmk_is_reported(self, tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr("invitation.builder.shutil.which", lambda _: None)
        with pytest.raises(BuildError, match="latexmk not found"):
            compile_pdf("\\documentclass{letter}", tmp_path / "out.pdf")

    def test_failed_latexmk_is_reported(self, tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr("invitation.builder.shutil.which", lambda _: "/usr/bin/latexmk")

        class Result:
            returncode = 12

        monkeypatch.setattr("invitation.builder.subprocess.run", lambda *a, **k: Result())
        with pytest.raises(BuildError, match="status 12"):
            compile_pdf("\\documentclass{letter}", tmp_path / "out.pdf")
