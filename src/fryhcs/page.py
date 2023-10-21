from fryhcs.element import Element
from fryhcs.utils import static_url
from fryhcs.config import fryconfig

class Page(object):
    def __init__(self):
        self.component_count = 0

    def add_component(self):
        self.component_count += 1
        return self.component_count


def render(element):
    if isinstance(element, Element):
        page = Page()
        element = element.render(page)
    elif callable(element) and getattr(element, '__name__', 'anonym')[0].isupper():
        page = Page()
        element = Element(element).render(page)
    return element


def html(content='', title='', lang='en', rootclass='', charset='utf-8', viewport="width=device-width, initial-scale=1.0", metas={}, properties={}, equivs={}):
    sep = '\n    '

    content = render(content)

    metas = sep.join(f'<meta name="{name}" content="{value}">'
                       for name, value in metas.items())
    properties = sep.join(f'<meta property="{property}" content="{value}">'
                            for property, value in properties.items())
    equivs = sep.join(f'<meta http-equiv="{equiv}" content="{value}">'
                            for equiv, value in equivs.items())
    importmap = f'''
    <script type="importmap">
      {{
        "imports": {{
          "fryhcs": "{static_url('js/fryhcs.js')}",
          "components/": "{static_url(fryconfig.js_url)}",
          "@/": "{static_url('/')}"
        }}
      }}
    </script>
    '''

    if fryconfig.debug:
        script = """
  <script type="module">
    let serverId = null;
    let eventSource = null;
    let timeoutId = null;
    function checkAutoReload() {
        if (timeoutId !== null) clearTimeout(timeoutId);
        timeoutId = setTimeout(checkAutoReload, 1000);
        if (eventSource !== null) eventSource.close();
        eventSource = new EventSource("{{autoReloadPath}}");
        eventSource.addEventListener('open', () => {
            console.log(new Date(), "Auto reload connected.");
            if (timeoutId !== null) clearTimeout(timeoutId);
            timeoutId = setTimeout(checkAutoReload, 1000);
        });
        eventSource.addEventListener('message', (event) => {
            const data = JSON.parse(event.data);
            if (serverId === null) {
                serverId = data.serverId;
            } else if (serverId !== data.serverId) {
                if (eventSource !== null) eventSource.close();
                if (timeoutId !== null) clearTimeout(timeoutId);
                location.reload();
                return;
            }
            if (timeoutId !== null) clearTimeout(timeoutId);
            timeoutId = setTimeout(checkAutoReload, 1000);
        });
    }
    checkAutoReload();
  </script>
"""
        autoreload = script.replace('{{autoReloadPath}}', fryconfig.check_reload_url)
    else:
        autoreload = ''

    if rootclass:
        rootclass = f' class="{rootclass}"'
    else:
        rootclass = ''

    return f'''\
<!DOCTYPE html>
<html lang={lang}{rootclass}>
  <head>
    <meta charset="{charset}">
    <title>{title}</title>
    <meta name="viewport" content="{viewport}">
    {metas}
    {properties}
    {equivs}
    <link rel="stylesheet" href="{static_url(fryconfig.css_url)}">
    {importmap}
  </head>
  <body>
    {content}
    <script>
      (async function () {{
        if ('fryfunctions$$' in window) {{
          for (const [script, fn] of window.fryfunctions$$) {{
            await fn(script);
          }}
        }}
      }})();
    </script>
    {autoreload}
  </body>
</html>
'''
