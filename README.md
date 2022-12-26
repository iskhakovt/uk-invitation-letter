UK visa invitation letter generator. ![PyPI](https://img.shields.io/pypi/v/uk-invitation-letter?style=flat-square)
===

Auto-generates UK tourist visa invitation letter.


---

### Requirements

* Python 3 with pip
* LaTeX

### Usage

1. Install the package:

```bash
pip3 install uk-invitation-letter
```

2. Create `data.yml` config file

Example:

```yaml
inviter: !entity
  name: Kayleigh H Welch
  address: !address
    lines:
      - 75 Hertingfordbury Road
      - NEWTON NG13 8QY
      # UK auto-added
  phone: "07758888305"
  email: slwzgtew2wj@temporary-mail.net

employer: !entity
  name: Jstory UK Ltd
  address: !address
    lines:
      - 89 Well Lane
      - PATTERDALE CA11 0LQ

embassy: !entity
  name: British Embassy Moscow
  address: !address
    lines:
      - Smolenskaya Naberezhnaya 10
      - Moscow 121099
      - Russian Federation

invitee: !entity
  name: # <first name> [<other names>]+ <last name>
    - Joseph Brodsky
    - Maria Sozzani
  pronoun: null # they/them/their by default
  relationship: friends

trip: !trip
  arrival_date: 2020-01-01
  departure_date: 2020-01-31
  reason: a short trip
  return_reason: null
  return_country: Russia
  financial_support: false
```

3. Run the generator

```bash
LATEX_BINARY=<path to latex binary> uk-invitation-letter
```

The output will be saved to `build/invitation.pdf`.
