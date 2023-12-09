from fryhcs.element import Element
from fryhcs.utils import static_url
from fryhcs.config import fryconfig

class Page(object):
    def __init__(self):
        # 记录当前已经处理的组件script元素列表，列表长度是当前正在处理的组件的ID
        self.components = []
        # 组件UUID（代表了js脚本）到组件实例ID的映射关系，jsid -> list of cid
        self.jsid2cids = {}
        # 组件实例ID到子组件引用/引用列表的映射关系, cid -> (refname -> childcid | list of childcid)
        self.cid2childrefs = {}

    def add_component(self, component):
        self.components.append(component)
        cid = len(self.components)
        self.cid2childrefs[cid] = {} 
        return cid

    def add_ref(self, cid, refname, childcid):
        childrefs = self.cid2childrefs[cid]
        if refname in childrefs:
            refs = childrefs[refname]
        else:
            refs = set()
            childrefs[refname] = refs
        refs.add(childcid)

    def child_refs(self, cid):
        origin = self.cid2childrefs.get(cid, {})
        refs = {}
        for name, ids in origin.items():
            if name.endswith(':a'):
                refs[name[:-2]] = list(ids)
            else:
                if len(ids) != 1:
                    raise RuntimeError(f"More than ONE ref value for '{name}'.")
                refs[name] = ids.pop()
        return refs

    def set_jsid2cid(self, jsid, cid): 
        if jsid in self.jsid2cids:
            cids = self.jsid2cids[jsid]
        else:
            cids = set()
            self.jsid2cids[jsid] = cids
        cids.add(cid)

    @property
    def jsids(self):
        return list(self.jsid2cids.keys())

    def components_of_script(self, jsid):
        return self.jsid2cids.get(jsid, [])


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
    components = '\n    '.join(str(c) for c in page.components)
    scripts = page.jsids
    if not scripts:
        hydrate_script = ""
    else:
        output = []
        for i, jsid in enumerate(scripts):
            if i == 0:
                output.append(f"import {{ hydrate as hydrate_{i}, hydrateAll }} from '{static_url(fryconfig.js_url)}{jsid}.js';")
            else:
                output.append(f"import {{ hydrate as hydrate_{i} }} from '{static_url(fryconfig.js_url)}{jsid}.js';")

            for cid in page.components_of_script(jsid):
                output.append(f"hydrates['{cid}'] = hydrate_{i};")
        all_scripts = '\n      '.join(output)

        hydrate_script = f"""
    <script type="module">
      let hydrates = {{}};
      {all_scripts}
      await hydrateAll(hydrates);
    </script>
"""

    metas = sep.join(f'<meta name="{name}" content="{value}">'
                       for name, value in metas.items())
    properties = sep.join(f'<meta property="{property}" content="{value}">'
                            for property, value in properties.items())
    equivs = sep.join(f'<meta http-equiv="{equiv}" content="{value}">'
                            for equiv, value in equivs.items())
    # no need to use importmap
    #importmap = f'''
    #<script type="importmap">
    #  {{
    #    "imports": {{
    #      "fryhcs": "{static_url('js/fryhcs.js')}"
    #    }}
    #  }}
    #</script>
    #'''

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
  </head>
  <body>
    {content}
    <div type="display:none;">
    {components}
    </div>
    {hydrate_script}
    {autoreload}
  </body>
</html>
'''
