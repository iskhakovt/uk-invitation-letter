import datetime
from collections.abc import Sequence
from typing import Annotated, Self

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


_PRONOUN_HINT = "Pronouns must be written as three non-empty parts separated by `/`, e.g. `she/her/her`"


def _split_pronoun(value: object) -> list[str]:
    if not isinstance(value, str):
        raise ValueError(_PRONOUN_HINT)
    parts = [part.strip() for part in value.split("/")]
    if len(parts) != 3 or not all(parts):
        raise ValueError(_PRONOUN_HINT)
    return parts


class Pronoun(RootModel):
    """Subject, object and determiner forms, written `she/her/her`. Defaults to they/them/their."""

    root: Annotated[tuple[NonBlankStr, NonBlankStr, NonBlankStr], BeforeValidator(_split_pronoun)] | None = None

    @property
    def subject(self) -> str:
        return self.root[0] if self.root else "they"

    @property
    def object(self) -> str:
        return self.root[1] if self.root else "them"

    @property
    def determiner(self) -> str:
        return self.root[2] if self.root else "their"


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
    pronoun: Pronoun = Field(default_factory=Pronoun)
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
