from pathlib import Path
import os

from .style import CSS
from .collector import Collector
from .color import theme_color_styles
from fryweb.config import fryconfig


class CssGenerator():
    def __init__(self):
        self.collector = Collector()

    def collect(self, tree, hash, attrfile):
        self.collector.collect_attrs(tree, hash, attrfile)
    
    def all_attrs(self):
        for file in fryconfig.build_root.rglob('*.attr'):
            with file.open('r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip();
                    if not line or line[0] == '#':
                        continue
                    k, v = line.split('=')
                    yield k, v

    def generate(self):
        fryconfig.css_file.parent.mkdir(parents=True, exist_ok=True)
        preflight = os.path.join(os.path.dirname(__file__), 'preflight.css')
        preflight = Path(preflight)
        with fryconfig.css_file.open('w', encoding='utf-8') as f:
            with preflight.open('r', encoding='utf-8') as pf:
                f.write(pf.read())
            f.write(theme_color_styles())
            from fryweb.css.plugin import plugin_basecss
            basecss = plugin_basecss()
            f.write(basecss)
            preflight = fryconfig.public_root / 'preflight.css'
            if preflight.is_file():
                with preflight.open('r', encoding='utf-8') as pf:
                    f.write(pf.read())
            preflight = fryconfig.public_root / 'css/preflight.css'
            if preflight.is_file():
                with preflight.open('r', encoding='utf-8') as pf:
                    f.write(pf.read())
            csses = []
            for key, value in self.all_attrs():
                css = CSS(key, value)
                if css.valid:
                    csses.append(css)
            for css in sorted(csses, key=lambda c: c.order):
                f.write(css.text())
