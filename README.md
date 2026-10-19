# UK visa invitation letter generator [![PyPI](https://img.shields.io/pypi/v/uk-invitation-letter?style=flat-square)](https://pypi.org/project/uk-invitation-letter/)

Writes a [UK Standard Visitor](https://www.gov.uk/standard-visitor) visa invitation letter for you.


---

### Requirements

* Python 3.11 or newer
* One of:
  * [Tectonic](https://tectonic-typesetting.github.io/), a single binary that fetches the LaTeX packages it needs by itself
  * A TeX distribution with `latexmk`, one of XeLaTeX, LuaLaTeX or pdfLaTeX, and the `garamond-libre`, `isodate`, `substr` and `fontaxes` packages (`tlmgr install garamond-libre isodate substr fontaxes`)

The examples below run the tool with [pipx](https://pipx.pypa.io/); `uvx uk-invitation-letter` or a plain `pip install` work just as well.

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
  name:  # <first name> [<other names>]+ <last name>
    - Joseph Brodsky
    - María Sozzani
  pronoun: they/them/their  # optional, e.g. she/her/her for a single invitee; a group is always they/them/their
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

The output will be saved to `invitation.pdf`. The default engine is XeLaTeX; pass `--engine tectonic`, `--engine lualatex` or `--engine pdflatex` to use another. pdfLaTeX uses Type 1 fonts with the T1 encoding, so it handles Latin-script text (including accents) but not other scripts; use one of the other engines for those.

Text from the data file is escaped for LaTeX automatically, so `&`, `%`, `#`, `_`, `~` and friends render literally. Names and address lines are never broken across lines. In those fields only, a `~` you type is kept as a non-breaking space: write `Mary~Ann Smith` so the short form of the name stays "Mary~Ann" rather than "Mary".

For repeated use, install it once with `pipx install uk-invitation-letter` and then invoke `uk-invitation-letter render ...` directly.
