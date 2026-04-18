import datetime
import re
from collections.abc import Sequence

import phonenumbers


def and_join(strs: Sequence[str]) -> str:
    if not strs:
        return ""
    if len(strs) == 1:
        return strs[0]
    if len(strs) == 2:
        return f"{strs[0]} and {strs[1]}"
    return ", ".join(strs[:-1]) + ", and~" + strs[-1]


def date_format(date: datetime.date) -> str:
    return f"{date.day}~{date:%B~%Y}"


def phone_format(phone: str) -> str:
    return use_non_breaking_space(
        phonenumbers.format_number(phonenumbers.parse(phone, "GB"), phonenumbers.PhoneNumberFormat.NATIONAL)
    )


def fix_floating_punctuation(s: str) -> str:
    return re.sub(r" +([,.;:!?])", r"\g<1>", s)


def use_non_breaking_space(s: str) -> str:
    return s.replace(" ", "~")
