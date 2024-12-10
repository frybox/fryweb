from pathlib import Path
import os

class FryConfig():

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
        if not self.debug:
            return ''
        if self.django_ok:
            from django.urls import reverse
            return reverse('fryweb:check_hotreload')
        if self.flask_ok:
            return flask_app.url_for('fryweb_check_hotreload')
        return ''

    @property
    def debug(self):
        return self.item('DEBUG', True)

    @property
    def static_root(self):
        return Path(self.item('FRYWEB_STATIC_ROOT', './public/'))

    @property
    def config_root(self):
        root_dir = None
        if self.django_ok:
            root_dir = getattr(django_settings, 'BASE_DIR', '')
        if self.flask_ok:
            root_dir = flask_app.root_path
        if root_dir:
            return Path(root_dir).resolve()
        else:
            return Path('.').resolve()

    @property
    def semantic_theme(self):
        return self.item('FRYWEB_SEMANTIC_THEME', None)

    @property
    def plugins(self):
        return self.item('FRYWEB_PLUGINS', [])

    @property
    def static_url(self, default='/static'):
        if self.django_ok:
            return getattr(django_settings, 'STATIC_URL', default)
        if self.flask_ok:
            return flask_app.static_url_path
        return default

    @property
    def js_file(self):
        return self.static_root / self.js_url

    @property
    def css_file(self):
        return self.static_root / self.css_url

fryconfig = FryConfig()
