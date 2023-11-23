from fryhcs.element import Element
from fryhcs.utils import static_url
from fryhcs.config import fryconfig

class Page(object):
    def __init__(self):
        self.component_count = 0
        self.uuid2cids = {}

    def add_component(self):
        self.component_count += 1
        return self.component_count

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
        output = ["let hydrates = {};"]
        for i, uuid in enumerate(scripts):
            output.append(f"import {{ hydrate as hydrate_{i} }} from '{static_url(fryconfig.js_url)}{uuid}.js';")
            for cid in page.components_of_script(uuid):
                output.append(f"hydrates['{cid}'] = hydrate_{i};")
        all_scripts = '\n      '.join(output)

        hydrate_script = f"""
    <script type="module">
      {all_scripts}
      const componentScripts = document.querySelectorAll('script[data-fryid]');
      let cid2script = {{}};
      let cids = [];
      for (const cscript of componentScripts) {{
        cscript.fryargs = {{}};
        for (const key in cscript.dataset) {{
          if (!key.startsWith('fry'))
            cscript.fryargs[key] = cscript.dataset[key];
        }}
        const cid = cscript.dataset.fryid;
        cid2script[cid] = cscript;
        cids.push(parseInt(cid));
      }}
      function collectRefs(element) {{
        if ('fryembed' in element.dataset) {{
          const embeds = element.dataset.fryembed;
          for (const embed of embeds.split(' ')) {{
            const cid = embed.split('/', 1)[0];
            const scriptElement = cid2script[cid];
            const prefix = cid + '/';
            const [_embedId, atype, ...args] = embed.substr(prefix.length).split('-');
            const arg = args.join('-');
            if (atype === 'ref') {{
              scriptElement.fryargs[arg] = element;
            }}
          }}
        }}
        for (const child of element.children) {{
          collectRefs(child);
        }}
      }}
      const rootScript = cid2script['1'];
      collectRefs(rootScript.parentElement);

      // 从后往前(从里往外)执行
      cids.sort((x,y)=>y-x);
      for (const cid of cids) {{
          const scid = ''+cid;
          await hydrates[scid](cid2script[scid]);
      }}
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
