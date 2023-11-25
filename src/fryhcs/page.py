from fryhcs.element import Element
from fryhcs.utils import static_url
from fryhcs.config import fryconfig

class Page(object):
    def __init__(self):
        # 记录当前已经处理的组件个数，也是当前正在处理的组件的ID
        self.component_count = 0
        # 组件UUID（代表了js脚本）到组件实例ID的映射关系，uuid -> list of cid
        self.uuid2cids = {}
        # 组件实例ID到子组件引用的映射关系, cid -> (refname -> childcid)
        self.cid2childrefs = {}
        # 组件实例ID到子组件全量引用的映射关系, cid -> (refname -> list of childcid)
        self.cid2childrefalls = {}

    def add_component(self):
        self.component_count += 1
        cid = self.component_count
        self.cid2childrefs[cid] = {} 
        self.cid2childrefalls[cid] = {}
        return cid

    def add_ref(self, cid, refname, childcid):
        childrefs = self.cid2childrefs[cid]
        if refname in childrefs:
            raise RuntimeError(f"More than one ref '{refname}', please use refall")
        childrefs[refname] = childcid

    def add_refall(self, cid, refname, childcid):
        childrefalls = self.cid2childrefalls[cid]
        if refname in childrefalls:
            refall = childrefalls[refname]
        else:
            refall = set()
            childrefalls[refname] = refall
        if childcid in refall:
            raise RuntimeError(f"More than one refall '{refname}' for child '{childcid}'")
        refall.add(childcid)

    def child_refs(self, cid):
        return self.cid2childrefs.get(cid, {})

    def child_refalls(self, cid):
        return self.cid2childrefalls.get(cid, {})

    def set_script(self, cid, uuid): 
        if uuid in self.uuid2cids:
            cids = self.uuid2cids[uuid]
        else:
            cids = set()
            self.uuid2cids[uuid] = cids
        cids.add(cid)

    @property
    def scripts(self):
        return list(self.uuid2cids.keys())

    def components_of_script(self, uuid):
        return self.uuid2cids.get(uuid, [])


def render(element, page=None):
    if not page:
        page = Page()
    if isinstance(element, Element):
        element = element.render(page)
    elif callable(element) and getattr(element, '__name__', 'anonym')[0].isupper():
        element = Element(element).render(page)
    return element


def html(content='', title='', lang='en', rootclass='', charset='utf-8', viewport="width=device-width, initial-scale=1.0", metas={}, properties={}, equivs={}):
    sep = '\n    '

    page = Page()
    content = render(content, page)
    scripts = page.scripts
    if not scripts:
        hydrate_script = ""
    else:
        output = []
        for i, uuid in enumerate(scripts):
            output.append(f"import {{ hydrate as hydrate_{i} }} from '{static_url(fryconfig.js_url)}{uuid}.js';")
            for cid in page.components_of_script(uuid):
                output.append(f"hydrates['{cid}'] = hydrate_{i};")
        all_scripts = '\n      '.join(output)

        hydrate_script = f"""
    <script type="module">
      let hydrates = {{}};
      {all_scripts}
      const scripts = document.querySelectorAll('script[data-fryid]');
      import {{hydrate}} from "{static_url('js/fryhcs.js')}";
      await hydrate(scripts, hydrates);
    </script>
"""

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
          "fryhcs": "{static_url('js/fryhcs.js')}"
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
    {hydrate_script}
    {autoreload}
  </body>
</html>
'''
