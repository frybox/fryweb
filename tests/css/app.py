# fry acb883ea9e81968a8e56488b429640b1312e44a3
from fryweb import html, Element
from flask import Flask
from random import randint

app = Flask(__name__)

@app.get('/')
def index():
    return html(App, title="fryweb CSS test", autoreload=False)


def App():
    c = Element(Content, {"class": "text-cyan-600 h-500px"})
    print(c.get_style('color'))
    print(c.get_style('height'))
    return Element("div", {"flex": True, "flex-col": True, "gap-4": True, "text-center": True, "h-sub,100vh,25px": True, "children": [Element(Content, {"value": (randint(0,2)), "class": "mb-4 mt-8"}), Element(Content, {"value": (randint(0,2))}), Element(Content, {"value": (randint(0,2))})]})

def Content(value=0):
    if value == 0:
        css = ["bg-indigo-300", 'text-xl', 'text-cyan-a9', 'hover:bg-indigo-600', 'hover:text-cyan-a10']
    elif value == 1:
        css = ["bg-sky-300", 'text-xl', 'text-pink-dark-5', 'hover:bg-sky-600', 'hover:text-pink-dark-a6']
    elif value == 2:
        css = ["bg-pink-300", 'text-xl', 'text-yellow-9', 'hover:bg-pink-600', 'hover:text-yellow-10']
    else:
        css = ["bg-purple-300", 'text-xl', 'text-green-600', 'hover:bg-purple-600', 'hover:text-green-300']

    return Element("span", {"call-client-script": ["app_Content", []], ":el": Element.ClientRef("el"), "@click": Element.ClientEmbed(0), **{ key: True for key in (css)}, "children": ["hello hello fryweb(", (value), ")"]})

if __name__ == '__main__':
    from fryweb import render
    print(render(App))
