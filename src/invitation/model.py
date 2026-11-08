"""What a letter is made of. Pure data: nothing here knows about LaTeX (see filters.py for that)."""

import calendar
import datetime
from collections.abc import Mapping
from typing import Annotated, Final, Self

from pydantic import BaseModel, BeforeValidator, Field, StringConstraints, field_validator, model_validator

from .util import parse_phone

# Free text entered by the user. Leading/trailing whitespace is noise and blank values are mistakes.
NonBlankStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
# Postal address, one line per entry.
Address = Annotated[tuple[NonBlankStr, ...], Field(min_length=1)]


def _one_or_many(value: object) -> object:
    """`name: Alice Smith` is shorthand for `name: [Alice Smith]`."""
    if value is None:
        raise ValueError("name must be a string or a list of strings")
    return [value] if isinstance(value, str) else value


_PRONOUN_HINT = "Pronouns must be written as three non-empty parts separated by `/`, e.g. `she/her/her`"


class Pronoun(BaseModel, frozen=True, extra="forbid"):
    """The three forms of a pronoun: `she` will travel, I will pay for `her` journey, and the object form `her`.

    Written in the data file as `she/her/her`; `null` or omitted means they/them/their.
    """

    subject: NonBlankStr
    object: NonBlankStr  # the grammatical object form; shadows nothing, annotations do not bind names
    determiner: NonBlankStr

    @model_validator(mode="before")
    @classmethod
    def from_slash_form(cls, value: object) -> object:
        if value is None:
            return THEY.model_dump()
        if isinstance(value, Mapping):  # keyword construction from Python
            return value
        if not isinstance(value, str):
            raise ValueError(_PRONOUN_HINT)
        parts = [part.strip() for part in value.split("/")]
        if len(parts) != 3 or not all(parts):
            raise ValueError(_PRONOUN_HINT)
        return dict(zip(("subject", "object", "determiner"), parts, strict=True))


THEY: Final[Pronoun] = Pronoun(subject="they", object="them", determiner="their")


# `residence` values the letter replaces with a fixed description; anything else is printed as written.
RESIDENCE_KEYWORDS: Final[frozenset[str]] = frozenset({"permit", "share code", "passport"})


class Inviter(BaseModel):
    name: NonBlankStr
    address: Address
    phone: NonBlankStr
    email: NonBlankStr
    status: NonBlankStr | None = None  # completes "I am ...", e.g. `a British citizen`
    residence: NonBlankStr | None = None
    proof_of_address: NonBlankStr | None = None

    @field_validator("phone")
    @classmethod
    def check_phone(cls, phone: str) -> str:
        parse_phone(phone)
        return phone

    @field_validator("status")
    @classmethod
    def drop_full_stop(cls, status: str | None) -> str | None:
        # The letter ends "I am ..." with its own full stop.
        if status is None:
            return None
        status = status.removesuffix(".").rstrip()
        if not status:
            raise ValueError("status must say more than a full stop")
        return status

    @field_validator("residence")
    @classmethod
    def normalise_residence_keyword(cls, residence: str | None) -> str | None:
        # Keywords match in any case; the template and `warnings` then compare against the lower-case form.
        if residence is not None and residence.casefold() in RESIDENCE_KEYWORDS:
            return residence.casefold()
        return residence


class Invitee(BaseModel):
    """The person or people being invited, and how the inviter knows them (`friend`, `parents`, ...)."""

    name: Annotated[tuple[NonBlankStr, ...], BeforeValidator(_one_or_many)]
    pronoun: Pronoun = THEY
    relationship: NonBlankStr

    @field_validator("name")
    @classmethod
    def check_someone_is_invited(cls, name: tuple[str, ...]) -> tuple[str, ...]:
        if not name:
            raise ValueError("at least one person must be invited")
        return name

    @model_validator(mode="after")
    def check_pronoun_fits(self) -> Self:
        # The letter refers to a group as they/them/their, so a pronoun only means something for one person.
        if len(self.name) > 1 and self.pronoun != THEY:
            raise ValueError("pronoun applies to a single invitee; a group is always referred to as they/them/their")
        return self


class Employer(BaseModel):
    name: NonBlankStr
    address: Address


class Embassy(BaseModel):
    name: NonBlankStr
    address: Address


# Appendix V: Visitor, V 17.2: a Standard Visitor is granted permission for up to 6 months. The rules don't
# say whether 6 months from 1 January ends on 30 June or 1 July, so leaving on the anniversary is warned about.
MAX_STAY_MONTHS: Final[int] = 6


def _add_months(day: datetime.date, months: int) -> datetime.date | None:
    """The same day `months` later, clamped to the end of a shorter month (31 Aug + 6 → 28/29 Feb).

    None when that is past the last date `datetime.date` can hold.
    """
    index = day.month - 1 + months
    year, month = day.year + index // 12, index % 12 + 1
    if year > datetime.MAXYEAR:
        return None
    return day.replace(year=year, month=month, day=min(day.day, calendar.monthrange(year, month)[1]))


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

    def warnings(self) -> tuple[str, ...]:
        """Problems that would weaken the application but don't stop the letter being written.

        These are warnings rather than validation errors so that data files that worked before still do.
        """
        found = []
        if self.inviter.residence == "permit":
            found.append(
                "inviter.residence: `permit` lists a biometric residence permit, but BRPs have expired and been "
                "replaced by eVisas; use `share code`"
            )
        anniversary = _add_months(self.trip.arrival_date, MAX_STAY_MONTHS)
        if anniversary is not None and self.trip.departure_date >= anniversary:
            found.append(
                f"trip.departure_date: a Standard Visitor can usually stay up to {MAX_STAY_MONTHS} months; "
                f"leave before {anniversary}"
            )
        return tuple(found)
