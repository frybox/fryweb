# fry e1c78f1de162301c1cb499f60ab5b2e48b5f43d3
from fryweb import html, Element
from flask import Flask

app = Flask(__name__)
app.config['FRYWEB_PLUGINS'] = ['daisyui']

def App():
    initial_count = 20
    return Element("div", {"call-client-script": ["app_App", [("initial_count", initial_count)]], "children": [Element("h1", {"text-cyan-500": True, "hover:text-cyan-600": True, "text-center": True, "mt-100px": True, "children": ["Hello Fryweb", !]}), Element("p", {"text-indigo-600": True, "text-center": True, "mt-9": True, "children": ["Count:", Element("span", {"text-cool/30": True, "children": [Element("span", {"*": Element.ClientEmbed(0), "children": [f"{initial_count}"]})]})]}), Element("div", {"flex": True, "w-full": True, "justify-center": True, "children": [Element("button", {"btn": True, "btn-cool": True, "@click": Element.ClientEmbed(1), "children": ["Increment"]})]})]})

@app.get('/')
def index():
    return html(App, "Hello")

