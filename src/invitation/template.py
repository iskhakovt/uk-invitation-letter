from typing import Final

TEMPLATE_YAML: Final = """\
inviter:
  name: <full name>
  address:
    - <line 1>
    - <line 2>
  phone: "<GB phone number>"
  email: <email>
  residence: share code  # optional: `permit` / `share code` / `passport` / custom
  proof_of_address: council tax bill  # optional

employer:  # optional
  name: <employer name>
  address:
    - <line 1>
    - <line 2>

embassy:
  name: <embassy name>
  address:
    - <line 1>
    - <line 2>

invitee:
  name:  # <first name> [<other names>]+ <last name>, use `~` for a non-breaking space
    - <full name>
  pronoun: null  # optional, they/them/their by default; otherwise e.g. she/her/her
  relationship: friend

trip:
  arrival_date: YYYY-MM-DD
  departure_date: YYYY-MM-DD
  reason: a short trip  # optional
  return_reason: to return home  # optional
  return_country: <country>  # optional
  financial_support: false

docs:  # optional extra documents
  - <document name>
"""
