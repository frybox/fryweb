# fry fda5a136033d44d3d3898c517046b8172460762b
from fryweb import html, Element
from flask import Flask

app = Flask(__name__)

def App():
    return Element("h1", {"text-cyan-500": True, "hover:text-cyan-600": True, "text-center": True, "mt-100px": True, "children": ["Hello Fryweb", !]})

@app.get('/')
def index():
    return html(App, "Hello")
