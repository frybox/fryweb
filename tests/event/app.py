# fry 4f28459f7ffd1a2852b33ef6c80d646151b739e6
from fryweb import Element, html
from flask import Flask

app = Flask(__name__)

@app.get('/')
def index():
    return html(App, title="Event", autoreload=False)

def App():
    return Element("div", {"call-client-script": ["app_App", []], "flex": True, "flex-col": True, "justify-center": True, "items-center": True, "children": [Element("h1", {"text-center": True, "text-sky-600": True, "children": ["Test Event to Client Component:", Element("span", {"*": Element.ClientEmbed(0), "children": [f"0"]})]}), Element(EventButton, {"@click": Element.ClientEmbed(1)})]})

def EventButton():
    return Element("div", {"text-center": True, "bg-indigo-300": True, "hover:bg-indigo-600": True, "w-100px": True, "h-30px": True, "mt-10": True, "cursor-pointer": True, "children": ["Click Me", !]})
