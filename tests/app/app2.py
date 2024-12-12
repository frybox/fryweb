# fry 657c0c9be91051fa079471939d2fbb1e5c664da4
from fryweb import html, Element
from flask import Flask

app = Flask(__name__)

def App():
    initial_count = 10
    return Element("div", {"children": [Element("h1", {"text-cyan-500": True, "hover:text-cyan-600": True, "text-center": True, "mt-100px": True, "children": ["Hello Fryweb", !]}), Element("p", {"text-indigo-600": True, "text-center": True, "mt-9": True, "children": ["Count:", (initial_count)]})]})

@app.get('/')
def index():
    return html(App, "Hello")
