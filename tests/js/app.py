# fry 5befeeeb09d80271f06c1b030f74895c0cabe2a3
# fry 1234567890123456789012345678901234567890123456789012345678901234
from fryweb import Element, html
from flask import Flask

app = Flask(__name__)

def Sub2(v, create, children=[]):
    return Element("div", {"call-client-script": ["app_Sub2", [("create", create)]], ":foo": Element.ClientRef("foo"), "children": [Element("p", {"children": ["Sub2:", (v)]}), Element("p", {"children": ["Sub2:", Element("span", {"*": Element.ClientEmbed(0), "children": [f"{v}"]})]}), (children)]})

def Sub1(bar, create, children=[]):
    return Element(Sub2, {"call-client-script": ["app_Sub1", []], "v": (bar), "create": create, "children": [(children)]})

def App():
    return Element(Sub1, {"call-client-script": ["app_App", []], "bar": "from app", "create": (False), "children": [Element("p", {"children": ["App:", Element("span", {"*": Element.ClientEmbed(0), "children": [f"0"]})]})]})

@app.get('/')
def index():
    return html(App, title="Test JS", autoreload=False)
