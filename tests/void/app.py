# fry 7e52a687e2e40da281b473c8058c23bf6f52f12d
from fryweb import html, Element
from flask import Flask

app = Flask(__name__)

def App():
    initial_count = 20
    return Element("div", {"call-client-script": ["app_App", [("initial", (initial_count))]], "children": [Element("h1", {":header": Element.ClientRef("header"), "text-cyan-500": True, "hover:text-cyan-600": True, "text-center": True, "mt-100px": True, "children": ["Hello Fryweb", !]}), Element("hr", {}), Element("p", {"text-indigo-600": True, "text-center": True, "mt-9": True, "title": f"hello {initial_count}", "children": ["Count:", Element("span", {"text-red-600": True, "children": [Element("span", {"*": Element.ClientEmbed(0), "children": [f"{initial_count}"]})]})]}), Element("hr", {}), Element("input", {"type": "hidden", "name": "aaa", "value": "bbb"}), Element("p", {"text-indigo-600": True, "text-center": True, "mt-9": True, "children": ["Double:", Element("span", {"text-red-600": True, "children": [Element("span", {"*": Element.ClientEmbed(1), "children": [f"{initial_count*2}"]})]})]}), Element("hr", {}), Element("input", {"type": "hidden", "name": "ccc", "value": "ddd"}), Element("div", {"flex": True, "w-full": True, "justify-center": True, "children": [Element("button", {"@click": Element.ClientEmbed(2), "class": "inline-flex items-center justify-center h-10 gap-2 px-5 text-sm font-medium tracking-wide text-white transition duration-300 rounded focus-visible:outline-none whitespace-nowrap bg-emerald-500 hover:bg-emerald-600 focus:bg-emerald-700 disabled:cursor-not-allowed disabled:border-emerald-300 disabled:bg-emerald-300 disabled:shadow-none", "children": ["Increment"]})]})]})

@app.get('/')
def index():
    return html(App, "Hello")
