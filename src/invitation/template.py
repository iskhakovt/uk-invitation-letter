from importlib import resources


def load_template_yaml() -> str:
    return resources.files("invitation").joinpath("template.yml").read_text(encoding="utf-8")
