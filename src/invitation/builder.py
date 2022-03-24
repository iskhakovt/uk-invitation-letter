import os
import pathlib
import subprocess
import jinja2
import yaml

from .model import Address, Entity, Trip
from .util import date_format, phone_format, fix_floating_punctuation


LATEX_BINARY = os.environ.get('LATEX_BINARY', 'xelatex')


def main():
    with open('data.yml') as config_file:
        config = yaml.full_load(config_file)

    template_env = jinja2.Environment(loader=jinja2.PackageLoader('invitation', 'templates'))
    template = template_env.get_template('invitation.tex.jinja')
    output_text = template.render(**config, date_format=date_format, phone_format=phone_format)
    output_text = fix_floating_punctuation(output_text)

    pathlib.Path('build').mkdir(exist_ok=True)

    with open('build/invitation.tex', 'w') as output_file:
        output_file.write(output_text)

    subprocess.call([LATEX_BINARY, '-output-directory', 'build', 'build/invitation.tex'])


if __name__ == '__main__':
    main()
