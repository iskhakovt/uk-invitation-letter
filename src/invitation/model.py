import datetime
from collections.abc import Sequence
from typing import Self

from pydantic import BaseModel, Field, RootModel, model_validator

from .util import and_join, use_non_breaking_space


class Address(RootModel):
    root: list[str]

    @model_validator(mode="after")
    def check_not_empty(self) -> Self:
        if not self.root:
            raise ValueError("Address must not be empty")
        return self

    def _lines(self) -> Sequence[str]:
        return [use_non_breaking_space(line) for line in self.root]

    def line(self) -> str:
        return ", ".join(self._lines())

    def multiline(self) -> str:
        return "\\\\\n".join(self._lines())


class Name(RootModel):
    root: str | list[str]

    @model_validator(mode="after")
    def check_not_empty(self) -> Self:
        if not self.root:
            raise ValueError("Name must not be empty")
        return self

    def _as_sequence(self) -> Sequence[str]:
        return [self.root] if isinstance(self.root, str) else self.root

    def full_name(self) -> str:
        return and_join([use_non_breaking_space(name) for name in self._as_sequence()])

    def short_name(self) -> str:
        return and_join([name.split(" ")[0] for name in self._as_sequence()])


class Pronoun(RootModel):
    root: str | None = None

    @model_validator(mode="after")
    def check_three_parts(self) -> Self:
        if self.root is not None and len(self.root.split("/")) != 3:
            raise ValueError("Pronouns must have three parts separated by `/`")
        return self

    def _part(self, idx: int, default: str) -> str:
        return self.root.split("/")[idx] if self.root else default

    @property
    def subject(self) -> str:
        return self._part(0, "they")

    @property
    def object(self) -> str:
        return self._part(1, "them")

    @property
    def determiner(self) -> str:
        return self._part(2, "their")


class Inviter(BaseModel):
    name: Name
    address: Address
    phone: str
    email: str
    residence: str | None = None
    proof_of_address: str | None = None


class Invitee(BaseModel):
    name: Name
    pronoun: Pronoun = Field(default_factory=Pronoun)
    relationship: str


class Employer(BaseModel):
    name: Name
    address: Address


class Embassy(BaseModel):
    name: Name
    address: Address


class Trip(BaseModel):
    arrival_date: datetime.date
    departure_date: datetime.date
    reason: str | None = None
    return_reason: str | None = None
    return_country: str | None = None
    financial_support: bool = False


class InvitationConfig(BaseModel):
    inviter: Inviter
    invitee: Invitee
    employer: Employer | None = None
    embassy: Embassy
    trip: Trip
    docs: tuple[str, ...] = ()
