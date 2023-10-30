from django.core.management.base import CommandError, LabelCommand
from fryhcs.utils import create_js_generator, create_css_generator
from fryhcs.fy.generator import fy_to_py
from pathlib import Path


class Command(LabelCommand):
    help = "Runs fryhcs commands"
    missing_args_message = """
Command argument is missing, please add one of the following:
  build - to compile .fy into production css and js
  fy2py - to compile .fy into .py file
Usage example:
  python manage.py fryhcs build
  python manage.py fryhcs fy2py FYFILE
"""

    def handle(self, *labels, **options):
        if len(labels) == 1 and labels[0] == 'build':
            return self.build()
        elif len(labels) == 2 and labels[0] == 'fy2py':
            return self.fy2py(labels[1])
        else:
            return "Wrong command, Usage: python manage.py fryhcs [build | fy2py FYFILE]"

    def build(self)
        output = []
        js_generator = create_js_generator()
        css_generator = create_css_generator()
        output.append("Processing css information in the following place:")
        output.append('')
        for file in css_generator.input_files:
            output.append(f"  {file}")
        output.append('')
        css_generator.generate()
        output.append("... Done.")
        output.append('')
        output.append(f"CSS file {css_generator.output_file} is regenerated.")
        output.append('')
        output.append("Processing js information in the following place:")
        output.append('')
        for file in js_generator.fileiter.all_files():
            output.append(f"  {file}")
        output.append('')
        js_generator.generate()
        output.append("... Done.")
        output.append('')
        output.append('')
        return '\n'.join(output)

    def fy2py(fyfile):
        path = Path(fyfile)
        if not path.is_file():
            return f"Wrong argument to fryhcs fy2py command: {fyfile} is not readable"
        with path.open('r') as f:
            data = f.read()
        return fy_to_py(data)
