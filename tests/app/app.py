# fry e379075040e1aefc6a64459b5a441912a48feec3
from fryweb import html, Element
from flask import Flask

app = Flask(__name__)

def App():
    initial_count = 20
    return Element("body", {"call-client-script": ["app_App", [("initial", (initial_count))]], "bg-hex-f5f5f5": True, "children": [Element("h1", {":header": Element.ClientRef("header"), "text-cyan-500": True, "hover:text-cyan-600": True, "text-center": True, "mt-100px": True, "children": ["Hello Fryweb", !]}), Element("p", {"text-indigo-600": True, "text-center": True, "mt-9": True, "title": f"hello {initial_count}", "children": ["Count:", Element("span", {"text-red-600": True, "children": [Element("span", {"*": Element.ClientEmbed(0), "children": [f"{initial_count}"]})]})]}), Element("p", {"text-indigo-600": True, "text-center": True, "mt-9": True, "children": ["Double:", Element("span", {"text-red-600": True, "children": [Element("span", {"*": Element.ClientEmbed(1), "children": [f"{initial_count*2}"]})]})]}), Element("div", {"flex": True, "w-full": True, "justify-center": True, "children": [Element("button", {"@click": Element.ClientEmbed(2), "class": "inline-flex items-center justify-center h-10 gap-2 px-5 text-sm font-medium tracking-wide text-white transition duration-300 rounded focus-visible:outline-none whitespace-nowrap bg-emerald-500 hover:bg-emerald-600 focus:bg-emerald-700 disabled:cursor-not-allowed disabled:border-emerald-300 disabled:bg-emerald-300 disabled:shadow-none", "children": ["Increment"]})]})]})

def Body():
    return Element("body", {"bg-hex-f5f5f5": True, "children": [Element(App, {})]})

@app.get('/')
def index():
    return html(App, "Hello")
