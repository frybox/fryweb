from pathlib import Path

from fryweb.config import fryconfig

import inspect
import sys

def fry_files():
    paths = set()
    syspath = [Path(p).resolve() for p in sys.path]
    paths.update(p.resolve() for p in syspath if p.is_dir())
    input_files = [(str(p), '**/*.fry') for p in paths]
    return input_files

def create_css_generator():
    # input_files = [(dir, '**/*.html') for dir in template_directories()]
    from fryweb.css.generator import CSSGenerator
    return CSSGenerator(fry_files(), fryconfig.css_file)

def create_js_generator():
    from fryweb.js.generator import JSGenerator
    return JSGenerator(fry_files(), fryconfig.js_file)


def static_url(path):
    return fryconfig.static_url.rstrip('/') + '/' + path.lstrip('/')

def component_name(fn):
    if inspect.isfunction(fn) or inspect.isclass(fn):
        return fn.__name__
    return str(fn)
