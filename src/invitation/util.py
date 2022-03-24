import re
import phonenumbers


def and_join(strs):
    if not strs:
        return None
    if len(strs) == 1:
        return strs[0]
    if len(strs) == 2:
        return '{} and {}'.format(strs[0], strs[1])
    return ', '.join(strs[:-1]) + ', and~' + strs[-1]


def date_format(date):
    return date.strftime('%-d~%B~%Y')


def phone_format(phone):
    return use_non_breaking_space(
            phonenumbers.format_number(
                phonenumbers.parse(phone, 'GB'),
                phonenumbers.PhoneNumberFormat.NATIONAL
            )
        )


def fix_floating_punctuation(s):
    return re.sub(r'\ +([^\w\s])', r'\g<1>', s)


def use_non_breaking_space(s):
    return re.sub(' ', '~', s)
