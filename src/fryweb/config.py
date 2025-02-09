from pathlib import Path
import os
import sys
import importlib
from collections.abc import Iterable
import inspect

def is_wsgi_app(app):
    # 检查对象是否可调用
    if not callable(app):
        return False

    # 检查参数签名
    sig = inspect.signature(app)
    params = list(sig.parameters.keys())
    # WSGI 应用的参数应该是 environ 和 start_response
    if len(params) != 2: # or params[0] != 'environ' or params[1] != 'start_response':
        return False

    # 尝试调用应用，确保它不会抛出异常
    try:
        # 创建一个示例的 environ 对象
        environ = {
            'REQUEST_METHOD': 'GET',
            'PATH_INFO': '/',
            'wsgi.version': (1, 0),
            'wsgi.url_scheme': 'http',
            'wsgi.input': '',
            'wsgi.errors': '',
            'wsgi.multithread': False,
            'wsgi.multiprocess': False,
            'wsgi.run_once': False,
        }
        
        # 简单的 start_response 函数
        def start_response(status, headers):
            pass
        
        # 尝试调用应用
        result = app(environ, start_response)
        result = isinstance(result, Iterable)
        return result
    except:
        pass
    return False

class FryConfig():
    def __init__(self):
        self.app_spec = ''

    def set_app_spec(self, app_spec=''):
        """
        fryweb采用flask指定模块和应用对象的方式，(fry dev/build/run)有一个可选参数（无需添加--app或-A），格式如下：

        ```
          [file/system/path/][python.module.path][:app_name]
        ```

        比如，`src/frydea.app:asgi_app`，将src目录添加到sys.path，然后从frydea包中import app模块，从中找到名为`asgi_app`的应用对象，使用这个应用对象响应用户请求。

        上述三个部分都是可选的，每一部分都有按照顺序查找的默认值。
        文件系统路径默认值：
        - 当前目录: ./
        - 源码目录: src/

        python模块路径默认值：
        - main
        - app
        - api

        应用对象名默认值：
        - app
        - api
        """
        self.app_spec = app_spec

    def add_app_syspaths(self):
        fspath, _, _ = self.app_spec.rpartition('/')
        if not fspath:
            syspaths = [Path('.').resolve(), Path('src').resolve()]
        else:
            syspaths = [Path(fspath).resolve()]
        for p in reversed(syspaths):
            p = str(p)
            if p not in sys.path:
                sys.path.insert(0, p)
        return syspaths

    def get_app_spec_string(self):
        self.add_app_syspaths()
        _, _, apppath = self.app_spec.rpartition('/')
        pypath, _, appname = apppath.partition(':')
        if not pypath:
            pypaths = ['main', 'app', 'api']
        else:
            pypaths = [pypath]
        for p in pypaths:
            try:
                module = importlib.import_module(p)
                pypath = p
                break
            except ModuleNotFoundError as e:
                if len(pypaths) == 1:
                    raise
                if e.name != p:
                    raise
                module = None
        if not module:
            raise RuntimeError(f"Can't find app module")
        if not appname:
            appnames = ['app', 'api']
        else:
            appnames = [appname]
        for name in appnames:
            instance = module
            try:
                for attr in name.split('.'):
                    instance = getattr(instance, attr)
                appname = name
                break
            except AttributeError:
                if len(appnames) == 1:
                    raise
                instance = None
        if not instance:
            raise RuntimeError(f"Can't find app object from module {module}")
        self._is_wsgi_app = is_wsgi_app(instance)
        return f'{pypath}:{appname}'

    @property
    def is_wsgi_app(self):
        return getattr(self, '_is_wsgi_app', False)

    def item(self, name, default):
        if name in os.environ:
            value = os.environ[name]
            if isinstance(default, (list, tuple)):
                value = value.split(':')
            return value
        return default

    @property
    def js_url(self):
        return self.item('FRYWEB_JS_URL', 'js/index.js')

    @property
    def css_url(self):
        return self.item('FRYWEB_CSS_URL', 'css/styles.css')

    @property
    def check_reload_url(self):
        return self.item('FRYWEB_RELOAD_URL', '__check_reload')

    @property
    def debug(self):
        return self.item('DEBUG', True)

    @property
    def static_root(self):
        """
        最终生成的静态资源目录
        """
        return Path(self.item('FRYWEB_STATIC_ROOT', './frystatic/')).resolve()

    @property
    def public_root(self):
        """
        项目中的静态资源，最终会在编译时拷贝到static_root
        """
        return Path(self.item('FRYWEB_PUBLIC_ROOT', './public/')).resolve()

    @property
    def build_root(self): 
        """
        编译时的临时编译目录，其中的内容在全量编译时会被清空
        """
        return Path(self.item('FRYWEB_BUILD_ROOT', './build/')).resolve()

    @property
    def semantic_theme(self):
        return self.item('FRYWEB_SEMANTIC_THEME', None)

    @property
    def plugins(self):
        return self.item('FRYWEB_PLUGINS', [])

    @property
    def static_url(self):
        """
        浏览器访问时使用的静态资源前缀，静态资源有可能通过web server直接响应
        """
        return self.item('FRYWEB_STATIC_URL', '/static')

    @property
    def js_file(self):
        return self.static_root / self.js_url

    @property
    def css_file(self):
        return self.static_root / self.css_url

    @property
    def version(self):
        return '0.3.7'

fryconfig = FryConfig()

#fryconfig.set_app(app_string)
