import datetime

from pydantic import BaseModel, RootModel, model_validator

from .util import and_join, use_non_breaking_space


class Address(RootModel):
    root: list[str]

    @model_validator(mode="after")
    def check_not_empty(self) -> "Address":
        if not self.root:
            raise ValueError("Address must not be empty")
        return self

    def __get_lines(self) -> list[str]:
        return list(map(use_non_breaking_space, self.root))

    def line(self) -> str:
        return ", ".join(self.__get_lines())

    def multiline(self) -> str:
        return "\\\\\n".join(self.__get_lines())


class Name(RootModel):
    root: str | list[str]

    @model_validator(mode="after")
    def check_not_empty(self) -> "Name":
        if not self.root:
            raise ValueError("Name must not be empty")
        return self

    def __as_list(self) -> list[str]:
        return [self.root] if isinstance(self.root, str) else self.root

    def full_name(self) -> str:
        return and_join(list(map(use_non_breaking_space, self.__as_list())))

    def short_name(self) -> str:
        return and_join(list(map(lambda name: name.split(" ")[0], self.__as_list())))


class Pronoun(RootModel):
    root: str | None = None

    @model_validator(mode="after")
    def check_three_parts(self) -> "Pronoun":
        if self.root is not None and len(self.root.split("/")) != 3:
            raise ValueError("Pronouns must have three parts separated by `/`")
        return self

    def __get_pronoun_part(self, idx: int, default: str) -> str:
        return self.root.split("/")[idx] if self.root else default

    def get_subject(self) -> str:
        return self.__get_pronoun_part(0, "they")

    def get_object(self) -> str:
        return self.__get_pronoun_part(1, "them")

    def get_determiner(self) -> str:
        return self.__get_pronoun_part(2, "their")


class Inviter(BaseModel):
    name: Name
    address: Address
    phone: str
    email: str
    residence: str | None = None
    proof_of_address: str | None = None


class Invitee(BaseModel):
    name: Name
    pronoun: Pronoun = Pronoun()
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
    docs: list[str] = []
