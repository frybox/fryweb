"""
    fryweb.cmdline
    ~~~~~~~~~~~~~~~~

    Command line interface.

    :copyright: Copyright 2023 by zenkj<juzejian@gmail.com>
    :license: MIT, see LICENSE for details.
"""


import fnmatch
import os
import sys
import time
import traceback
import psutil
import signal
import typing as t
from itertools import chain
from pathlib import Path
import multiprocessing
import uvicorn
from uvicorn.main import Config as UvicornConfig, Server, ChangeReload, Multiprocess
from starlette.staticfiles import StaticFiles

import click

from fryweb.config import fryconfig
from fryweb.fry.generator import FryGenerator

import logging

logger = logging.getLogger(__name__)

# The various system prefixes where imports are found. Base values are
# different when running in a virtualenv. All reloaders will ignore the
# base paths (usually the system installation). The stat reloader won't
# scan the virtualenv paths, it will only include modules that are
# already imported.
prefix = {sys.base_prefix, sys.base_exec_prefix, sys.prefix, sys.exec_prefix}

if hasattr(sys, "real_prefix"):
    # virtualenv < 20
    prefix.add(sys.real_prefix)

_stat_ignore_scan = tuple(prefix)
del prefix
_ignore_common_dirs = {
    "__pycache__",
    ".git",
    ".hg",
    ".tox",
    ".nox",
    ".pytest_cache",
    ".mypy_cache",
}


def _remove_by_pattern(paths, exclude_patterns):
    for pattern in exclude_patterns:
        paths.difference_update(fnmatch.filter(paths, pattern))


def _find_stat_paths(extra_files, exclude_patterns) -> t.Iterable[str]:
    """Find paths for the stat reloader to watch. Returns imported
    module files, Python files under non-system paths. Extra files and
    Python files under extra directories can also be scanned.

    System paths have to be excluded for efficiency. Non-system paths,
    such as a project root or ``sys.path.insert``, should be the paths
    of interest to the user anyway.
    """
    paths = set()

    for path in chain(list(sys.path), extra_files):
        path = os.path.abspath(path)

        if os.path.isfile(path):
            # zip file on sys.path, or extra file
            continue

        parent_has_py = {os.path.dirname(path): True}

        for root, dirs, files in os.walk(path):
            # Optimizations: ignore system prefixes, __pycache__ will
            # have a py or pyc module at the import path, ignore some
            # common known dirs such as version control and tool caches.
            if (
                root.startswith(_stat_ignore_scan)
                or os.path.basename(root) in _ignore_common_dirs
            ):
                dirs.clear()
                continue

            has_py = False

            for name in files:
                if name.endswith('.fry'):
                    has_py = True
                    paths.add(os.path.join(root, name))
                elif name.endswith((".py", ".pyc")):
                    has_py = True

            # Optimization: stop scanning a directory if neither it nor
            # its parent contained Python files.
            if not (has_py or parent_has_py[os.path.dirname(root)]):
                dirs.clear()
                continue

            parent_has_py[root] = has_py

    _remove_by_pattern(paths, exclude_patterns)
    return paths

class BuilderLoop:
    def __init__(
        self,
        extra_files = None,
        exclude_patterns = None,
        interval = 1,
    ) -> None:
        self.extra_files: set[str] = {os.path.abspath(x) for x in extra_files or ()}
        self.exclude_patterns: set[str] = set(exclude_patterns or ())
        self.interval = interval

    def __enter__(self):
        """Do any setup, then run one step of the watch to populate the
        initial filesystem state.
        """
        self.mtimes: dict[str, float] = {}
        self.process = psutil.Process()
        self.run_step()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):  # type: ignore
        """Clean up any resources associated with the reloader."""
        pass

    def parent_ok(self):
        # psutil.Process.parent()中会处理父进程ID被重用的情况
        # 但不会处理unix中父进程死掉后，父进程改为init(pid=1)进程的情况
        parent = self.process.parent()
        if not parent or parent.pid == 1:
            return False
        return True

    def run(self) -> None:
        """Continually run the watch step, sleeping for the configured
        interval after each step.
        """
        while self.parent_ok():
            self.run_step()
            time.sleep(self.interval)

    def run_step(self) -> None:
        """Run one step for watching the filesystem. Called once to set
        up initial state, then repeatedly to update it.
        """
        changed = set()
        for name in _find_stat_paths(self.extra_files, self.exclude_patterns):
            try:
                mtime = os.stat(name).st_mtime
            except OSError:
                continue

            old_time = self.mtimes.get(name)

            if old_time is None:
                self.mtimes[name] = mtime
                continue

            if mtime > old_time:
                changed.add(name)
                self.mtimes[name] = mtime
        if changed:
            logger.info(f" * Detected change in {changed!r}, building")
            generator = FryGenerator(changed, clean=False)
            generator.generate()

def run_builder_loop():
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    builder = BuilderLoop()
    with builder:
        builder.run()


class WithStaticFiles:
    def __init__(self, app):
        self.app = app
        self.staticfiles_app = StaticFiles(directory=fryconfig.static_root)

    async def __call__(self, scope, receive, send):
        path = scope['path']
        if path.startswith(fryconfig.static_url):
            await self.staticfiles_app(scope, receive, send)
        else:
            await self.app(scope, receive, send)


class Config(UvicornConfig):
    def load(self):
        super().load()
        self.loaded_app = WithStaticFiles(self.loaded_app)


@click.group()
def cli():
    pass


@click.command()
@click.argument("app_spec", default='', required=False)
def build(app_spec):
    fryconfig.set_app_spec(app_spec)
    fryconfig.add_app_syspaths()
    generator = FryGenerator()
    generator.generate()


@click.command(short_help="Run a development server.")
@click.option("--host", "-h", default="127.0.0.1", help="The interface to bind to.")
@click.option("--port", "-p", default=6000, help="The port to bind to.")
@click.argument("app_spec", default='', required=False)
def dev(host, port, app_spec):
    fryconfig.set_app_spec(app_spec)
    fryconfig.add_app_syspaths()
    generator = FryGenerator()
    generator.generate()

    app_spec = fryconfig.get_app_spec_string()
    process = multiprocessing.Process(target=run_builder_loop)
    process.start()
    interface = 'wsgi' if fryconfig.is_wsgi_app else 'auto'
    config = Config(
        app=app_spec,
        host=host,
        port=port,
        reload=True,
        interface=interface,
    )
    server = Server(config=config)
    try:
        sock = config.bind_socket()
        ChangeReload(config, target=server.run, sockets=[sock]).run()
    except KeyboardInterrupt:
        print("dev process keyboardinteger")
        pass
    finally:
        if config.uds and os.path.exists(config.uds):
            os.remove(config.uds)
    if not server.started:
        logger.info("bye.")
        psutil.Process().terminate()


@click.command()
@click.option("--host", "-h", default="127.0.0.1", help="The interface to bind to.")
@click.option("--port", "-p", default=6000, help="The port to bind to.")
@click.option("--workers", "-w", default=1, help="Number of worker processes")
@click.argument("app_spec", default='', required=False)
def run(host, port, workers, app_spec):
    fryconfig.set_app_spec(app_spec)
    app_spec = fryconfig.get_app_spec_string()
    interface = 'wsgi' if fryconfig.is_wsgi_app else 'auto'
    config = Config(
        app=app_spec,
        host=host,
        port=port,
        workers=workers,
        reload=False,
        interface=interface,
    )
    server = Server(config=config)
    try:
        if config.workers > 1:
            sock = config.bind_socket()
            Multiprocess(config, target=server.run, sockets=[sock]).run()
        else:
            server.run()
    except KeyboardInterrupt:
        pass
    finally:
        if config.uds and os.path.exists(config.uds):
            os.remove(config.uds)
    if not server.started and config.workers == 1:
        sys.exit(3)


@click.command()
@click.argument("project_dir", default=None, required=False)
def init(project_dir):
    pass

@click.command()
def install():
    pass

@click.command()
def pyinstall():
    pass

@click.command()
def jsinstall():
    pass

@click.command()
def pyadd():
    pass

@click.command()
def jsadd():
    pass

cli.add_command(dev)
cli.add_command(build)
cli.add_command(run)
cli.add_command(init)
cli.add_command(install)
cli.add_command(pyinstall)
cli.add_command(jsinstall)
cli.add_command(pyadd)
cli.add_command(jsadd)

if __name__ == '__main__':
    cli()

# @click.command("topy", short_help="Convert specified .fry file into .py file.")
# @click.argument("fryfile")
# def topy_command(fryfile):
#     """Convert specified .fry file into .py file."""
#     from fryweb.fry.generator import fry_to_py
#     path = Path(fryfile)
#     if not path.is_file():
#         print(f"Error: can't open file '{fryfile}'.")
#         sys.exit(1)
#     with path.open('r', encoding='utf-8') as f:
#         data = f.read()
#     source = fry_to_py(data, path)
#     try:
#         from pygments.formatters.terminal import TerminalFormatter
#         from pygments.lexers import PythonLexer
#         from pygments import highlight
#         lexer = PythonLexer()
#         fmter = TerminalFormatter(linenos=True)
#         click.echo(highlight(source, lexer, fmter))
#     except ImportError:
#         lines = source.splitlines()
#         if lines:
#             prefix_len = len(str(len(lines)))
#             source = '\n'.join([f'{i:0{prefix_len}}: {line}' for i, line in zip(range(1, len(lines)+1), lines)])
#         click.echo(source)
# 
# 
# @click.command("tojs", short_help="Convert specified .fry file into .js file(s).")
# @click.argument("fryfile")
# @click.argument("jsdir")
# def tojs_command(fryfile, jsdir):
#     """Convert specified .fry file into .js file(s)."""
#     from fryweb.js.generator import JSGenerator
#     path = Path(fryfile)
#     if not path.is_file():
#         print(f"Error: can't open file '{fryfile}'.")
#         sys.exit(1)
#     generator = JSGenerator([fryfile], jsdir)
#     count = generator.generate()
#     if count == 0:
#         print(f"No js information in '{fryfile}'.")
#     else:
#         print(f"{count} js files from '{fryfile}' are generated into directory '{jsdir}'")
# 
# 
# @click.command("tocss", short_help="Convert specified .fry file into style.css file.")
# @click.option("-p", "--plugin", multiple=True, help="Specify a plugin to be loaded")
# @click.argument("fryfile")
# @click.argument("cssfile")
# def tocss_command(plugin, fryfile, cssfile):
#     """Convert specified .fry file into style.css file."""
#     if plugin:
#         sys.path.insert(0, '')
#         plugins = ':'.join(plugin)
#         os.environ['FRYWEB_PLUGINS'] = plugins
#     from fryweb.css.generator import CSSGenerator
#     path = Path(fryfile)
#     if not path.is_file():
#         print(f"Error: can't open file '{fryfile}'.")
#         sys.exit(1)
#     generator = CSSGenerator([fryfile], cssfile)
#     generator.generate()
#     print(f"styles from '{fryfile}' are generated into file '{cssfile}'.")
# 
# 
# @click.command("run", short_help="Convert specified .fry file into .py file and execute it.")
# @click.option("-m", "module", default=None, help="Specify a module to be run")
# @click.argument("fryfile", default=None, required=False, type=click.Path(exists=True, resolve_path=True))
# def run_command(module, fryfile):
#     """Convert specified .fry file into .py file and execute it."""
#     from runpy import run_module
#     if module and fryfile:
#         click.echo("ONLY ONE of -m MODULE and PYXFILE can be specified.")
#         return
#     if module:
#         sys.path.insert(0, '')
#     elif fryfile:
#         path = Path(fryfile)
#         if path.is_dir():
#             sys.path.insert(0, str(path))
#             module = '__main__'
#         elif path.suffix in ('.py', '.pyc', '.fry'):
#             dir = path.parent
#             sys.path.insert(0, str(dir))
#             module = path.stem
#         else:
#             click.echo("PYXFILE should be .py, .pyc or .fry file.")
#             return
#     else:
#         click.echo("one of -m MODULE and PYXFILE should be specified.")
#         return
#     _m = run_module(module, run_name='__main__')
# 
# 
# @click.command("hl", short_help="Highlight specified .fry file based on pygments.")
# @click.argument("fryfile", default=None, required=False, type=click.Path(exists=True, resolve_path=True))
# def hl_command(fryfile):
#     """Highlight specified .fry file based on pygments."""
#     try:
#         from pygments.formatters.terminal import TerminalFormatter
#         from pygments import highlight
#     except ImportError:
#         click.echo("Pygments is not installed, install it via `pip install pygments`")
#         return
#     from fryweb.fry.frylexer import FryLexer
#     lexer = FryLexer()
#     fmter = TerminalFormatter()
#     with open(fryfile, 'r', encoding='utf-8') as f:
#         source = f.read()
#     click.echo(highlight(source, lexer, fmter))