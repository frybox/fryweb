from pathlib import Path
import os
import sys
import importlib

class FryConfig():

    def set_app(self, app_string=''):
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
        fspath, _, apppath = app_string.rpartition('/')
        pypath, _, appname = apppath.partition(':')
        if not fspath:
            syspaths = [Path('.').resolve(), Path('src').resolve()]
        else:
            syspaths = [Path(fspath).resolve()]
        for p in reversed(syspaths):
            sys.path.insert(0, str(p))
        if not pypath:
            pypaths = ['main', 'app', 'api']
        else:
            pypaths = [pypath]
        for p in pypaths:
            try:
                module = importlib.import_module(p)
                break
            except:
                module = None
        if not module:
            raise RuntimeError(f"Can't import app module")
        if not appname:
            appnames = ['app', 'api']
        else:
            appnames = [appname]
        for name in appnames:
            instance = module
            try:
                for attr in name.split('.'):
                    instance = getattr(instance, attr)
                break
            except AttributeError:
                instance = None
        self.loaded_app = instance
        if not instance:
            raise RuntimeError(f"Can't find app object from module {module}")
        if hasattr(self.loaded_app, '__file__'):
            self.app_dir = Path(self.loaded_app.__file__).parent

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
        return Path(self.item('FRYWEB_STATIC_ROOT', './static/')).resolve()

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

fryconfig = FryConfig()

#fryconfig.set_app(app_string)
