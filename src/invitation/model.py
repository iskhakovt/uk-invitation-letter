import datetime
from collections.abc import Mapping, Sequence
from typing import Annotated, Final, Self

from pydantic import BaseModel, BeforeValidator, Field, RootModel, StringConstraints, field_validator, model_validator

from .util import Tex, and_join, parse_phone, tex_nobreak

# Free text entered by the user. Leading/trailing whitespace is noise and blank values are mistakes.
NonBlankStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
NonEmptyStrList = Annotated[list[NonBlankStr], Field(min_length=1)]


class Address(RootModel):
    root: NonEmptyStrList

    def _lines(self) -> Sequence[Tex]:
        return [tex_nobreak(line) for line in self.root]

    def line(self) -> Tex:
        return Tex(", ".join(self._lines()))

    def multiline(self) -> Tex:
        return Tex("\\\\\n".join(self._lines()))


def _one_or_many(value: object) -> object:
    if value is None:
        raise ValueError("Name must be a string or a list of strings")
    return [value] if isinstance(value, str) else value


class Name(RootModel):
    """One name, or several for a joint letter. A single string is accepted as shorthand for a one-item list."""

    root: Annotated[NonEmptyStrList, BeforeValidator(_one_or_many)]

    def full_name(self) -> Tex:
        return Tex(and_join([tex_nobreak(name) for name in self.root]))

    def short_name(self) -> Tex:
        return Tex(and_join([tex_nobreak(name.split(" ")[0]) for name in self.root]))


class Pronoun(BaseModel, frozen=True):
    """The three forms a letter needs: `she` will travel, I will assist `her`, `her` savings.

    Written in the data file as `she/her/her`; `null` or omitted means they/them/their.
    """

    subject: NonBlankStr
    object: NonBlankStr
    determiner: NonBlankStr

    @model_validator(mode="before")
    @classmethod
    def from_slash_form(cls, value: object) -> object:
        if value is None:
            return _THEY_FORMS
        if not isinstance(value, str):
            return value
        parts = value.split("/")
        if len(parts) != 3:
            raise ValueError("write pronouns as three parts separated by `/`, e.g. `she/her/her`")
        return dict(zip(("subject", "object", "determiner"), parts, strict=True))


_THEY_FORMS: Final[Mapping[str, str]] = {"subject": "they", "object": "them", "determiner": "their"}
THEY: Final[Pronoun] = Pronoun.model_validate(_THEY_FORMS)


class Inviter(BaseModel):
    name: Name
    address: Address
    phone: NonBlankStr
    email: NonBlankStr
    residence: NonBlankStr | None = None
    proof_of_address: NonBlankStr | None = None

    @field_validator("phone")
    @classmethod
    def check_phone(cls, phone: str) -> str:
        parse_phone(phone)
        return phone


class Invitee(BaseModel):
    name: Name
    pronoun: Pronoun = THEY
    relationship: NonBlankStr


class Employer(BaseModel):
    name: Name
    address: Address


class Embassy(BaseModel):
    name: Name
    address: Address


class Trip(BaseModel):
    arrival_date: datetime.date
    departure_date: datetime.date
    reason: NonBlankStr | None = None
    return_reason: NonBlankStr | None = None
    return_country: NonBlankStr | None = None
    financial_support: bool = False

    @model_validator(mode="after")
    def check_dates(self) -> Self:
        if self.departure_date < self.arrival_date:
            raise ValueError(
                f"departure_date ({self.departure_date}) must not be before arrival_date ({self.arrival_date})"
            )
        return self


class InvitationConfig(BaseModel):
    inviter: Inviter
    invitee: Invitee
    employer: Employer | None = None
    embassy: Embassy
    trip: Trip
    docs: tuple[NonBlankStr, ...] = ()
