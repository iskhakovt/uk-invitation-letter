import datetime
from collections.abc import Sequence
from typing import Annotated, Self

from pydantic import AfterValidator, BaseModel, Field, RootModel, StringConstraints, field_validator, model_validator

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


class Name(RootModel):
    root: NonBlankStr | NonEmptyStrList

    def _as_sequence(self) -> Sequence[str]:
        return [self.root] if isinstance(self.root, str) else self.root

    def full_name(self) -> Tex:
        return Tex(and_join([tex_nobreak(name) for name in self._as_sequence()]))

    def short_name(self) -> Tex:
        return Tex(and_join([tex_nobreak(name.split(" ")[0]) for name in self._as_sequence()]))


def _normalise_pronoun(value: str) -> str:
    parts = [part.strip() for part in value.split("/")]
    if len(parts) != 3 or not all(parts):
        raise ValueError("Pronouns must have three non-empty parts separated by `/`, e.g. `she/her/her`")
    return "/".join(parts)


class Pronoun(RootModel):
    root: Annotated[str, AfterValidator(_normalise_pronoun)] | None = None

    def _parts(self) -> tuple[str, str, str]:
        if self.root is None:
            return ("they", "them", "their")
        subject, obj, determiner = self.root.split("/")
        return (subject, obj, determiner)

    @property
    def subject(self) -> str:
        return self._parts()[0]

    @property
    def object(self) -> str:
        return self._parts()[1]

    @property
    def determiner(self) -> str:
        return self._parts()[2]


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
