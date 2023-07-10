UK visa invitation letter generator [![PyPI](https://img.shields.io/pypi/v/uk-invitation-letter?style=flat-square)](https://pypi.org/project/uk-invitation-letter/)
===

Writes a [UK Standard Visitor](https://www.gov.uk/standard-visitor) visa invitation letter for you.


---

### Requirements

* Python 3 with pip
* LaTeX with OpenType font support, e.g. XeLaTeX

### Usage

1. Install the package.

```bash
pip3 install uk-invitation-letter
```

2. Create `data.yml` config file.

Example:

```yaml
inviter: !entity
  name: Kayleigh H Welch
  address: !address
    lines:
      - 75 Hertingfordbury Road
      - Newton NG13 8QY
      # UK auto-added
  phone: "07758888305"
  email: noreply@temporary-mail.net

employer: !entity
  name: Jstory UK Ltd
  address: !address
    lines:
      - 89 Well Lane
      - Patterdale CA11 0LQ

embassy: !entity
  name: British Consulate General New York
  address: !address
    lines:
      - 885 2nd Ave
      - New York
      - NY 10017
      - United States

invitee: !entity
  name: # <first name> [<other names>]+ <last name>, use `~` for a non-breaking space
    - Joseph Brodsky
    - Maria Sozzani
  pronoun: null # they/them/their by default
  relationship: friends

trip: !trip
  arrival_date: 2020-01-01
  departure_date: 2020-01-31
  reason: a short trip
  return_reason: null
  return_country: the US
  financial_support: false
```

3. Run the generator.

```bash
LATEX_BINARY=<path to latex binary> uk-invitation-letter
```

The output will be saved to `build/invitation.pdf`.
