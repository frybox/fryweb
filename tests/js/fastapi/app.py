# fry 33cc6092987e89eea228ce3afcc2fbf2378cf6c6
# Generated by fryweb, DO NOT EDIT THIS FILE!

from fryweb import Element, html
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI()

def Sub2(v, create, children=[]):
    return Element("div", {"call-client-script": ["app_Sub2", [("create", create)]], ":foo": Element.ClientRef("foo"), "children": [Element("p", {"children": ["Sub2:", (v)]}), Element("p", {"children": ["Sub2:", Element("span", {"*": Element.ClientEmbed(0), "children": [f"{v}"]})]}), (children)]})

def Sub1(bar, create, children=[]):
    return Element(Sub2, {"call-client-script": ["app_Sub1", []], "v": (bar), "create": create, "children": [(children)]})

def App():
    return Element(Sub1, {"call-client-script": ["app_App", []], "bar": "from app", "create": (False), "children": [Element("p", {"children": ["App:", Element("span", {"*": Element.ClientEmbed(0), "children": [f"0"]})]})]})

@app.get('/', response_class=HTMLResponse)
async def index():
    return html(App, title="Test JS", autoreload=False)