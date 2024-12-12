# fry f34a697e819f9a07d0c10e67182c6f8f3721de58
from fryweb import html, Element
from flask import Flask

app = Flask(__name__)

def App():
    initial_count = 10
    return Element("div", {"call-client-script": ["app3_App", [("initial", (initial_count))]], "children": [Element("h1", {"text-cyan-500": True, "hover:text-cyan-600": True, "text-center": True, "mt-100px": True, "children": ["Hello Fryweb", !]}), Element("p", {"text-indigo-600": True, "text-center": True, "mt-9": True, "children": ["Count:", Element("span", {"text-red-600": True, "children": [Element("span", {"*": Element.ClientEmbed(0), "children": [f"{initial_count}"]})]})]}), Element("div", {"flex": True, "w-full": True, "justify-center": True, "children": [Element("button", {"type": "button", "@click": Element.ClientEmbed(1), "mt-9": True, "px-2": True, "rounded": True, "border": True, "bg-indigo-400": True, "hover:bg-indigo-600": True, "children": ["Increment"]})]})]})

@app.get('/')
def index():
    return html(App, "Hello")
