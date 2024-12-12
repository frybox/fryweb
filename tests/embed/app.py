# fry 759833b20df3381330fdbc5abe462348a1750dae
from flask import Flask
from fryweb import Element, html

app = Flask(__name__)

@app.get('/')
def index():
    return html(App, autoreload=False)

def App():
    return Element("div", {"call-client-script": ["app_App", []], "children": [Element("div", {"children": [Element("span", {"*": Element.ClientEmbed(0), "children": [f"这是一个&lt;strong&gt;text嵌入&lt;/strong&gt;"]})]}), Element("div", {"!": Element.ClientEmbed(1), "children": [f"""这是一个<strong>html嵌入</strong>"""]}), Element("div", {"children": [Element("p", {"children": ["hello world"]})]})]})