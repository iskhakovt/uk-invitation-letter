# UK visa invitation letter generator [![PyPI](https://img.shields.io/pypi/v/uk-invitation-letter?style=flat-square)](https://pypi.org/project/uk-invitation-letter/)

Writes a [UK Standard Visitor](https://www.gov.uk/standard-visitor) visa invitation letter for you.


---

### Requirements

* Python 3 with [pipx](https://pipx.pypa.io/)
* LaTeX with OpenType font support, e.g. XeLaTeX, and latexmk

### Usage

1. Create a `data.yml` config file. Generate a starting template with:

```bash
pipx run uk-invitation-letter gen > data.yml
```

Example:

```yaml
inviter:
  name: Kayleigh H Welch
  address:
    - 75 Hertingfordbury Road
    - Newton NG13 8QY
  phone: "07758888305"
  email: noreply@temporary-mail.net
  residence: share code  # optional: `permit` / `share code` / `passport` / custom
  proof_of_address: council tax bill  # optional

employer:
  name: Jstory UK Ltd
  address:
    - 89 Well Lane
    - Patterdale CA11 0LQ

embassy:
  name: British Consulate General New York
  address:
    - 885 2nd Ave
    - New York
    - NY 10017
    - United States

invitee:
  name:  # <first name> [<other names>]+ <last name>, use `~` for a non-breaking space
    - Joseph Brodsky
    - Maria Sozzani
  pronoun: they/them/their  # optional, they/them/their by default
  relationship: friends

trip:
  arrival_date: 2026-01-01
  departure_date: 2026-01-31
  reason: a short trip  # optional
  return_reason: to circumnavigate the globe  # optional
  return_country: the US  # optional
  financial_support: false

docs:  # optional extra documents
  - table tennis match result sheet
```

2. Render the letter:

```bash
pipx run uk-invitation-letter render --data data.yml --output invitation.pdf
```

The output will be saved to `invitation.pdf`. Pass `--engine lualatex` if you prefer LuaLaTeX (default is XeLaTeX).

For repeated use, install it once with `pipx install uk-invitation-letter` and then invoke `uk-invitation-letter render ...` directly.
