# fry 57df7139083c3efed96a364e6c93f9b738c9d7f4
# Generated by fryweb, DO NOT EDIT THIS FILE!
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fryweb import Element, html

app = FastAPI()

@app.get('/', response_class=HTMLResponse)
async def index():
    return html(App, autoreload=False)

def App():
    data = '<script>这是脚本</script>'
    return Element("div", {"call-client-script": ["app_App", [("data", data)]], "children": [Element("div", {"children": [Element("span", {"*": Element.ClientEmbed(0), "children": [f"这是一个&lt;strong&gt;text嵌入&lt;/strong&gt;"]})]}), Element("div", {"!": Element.ClientEmbed(1), "children": [f"""这是一个<strong>html嵌入</strong>"""]}), Element("div", {"children": [Element("p", {"children": ["hello world"]})]})]})