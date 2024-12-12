# fry f0ca2afd6ea61ab32f19dd54245ee83222508866
from fryweb import Element, html
from flask import Flask

app = Flask(__name__)

@app.get('/')
def index():
    return html(RefApp, title="test ref", autoreload=False)

def Refed():
    return Element("div", {"call-client-script": ["app_Refed", []], "children": ["hello world"]})

def RefApp():
    return Element("div", {"call-client-script": ["app_RefApp", []], "w-full": True, "h-100vh": True, "flex": True, "flex-col": True, "gap-y-10": True, "justify-center": True, "items-center": True, "children": [Element("p", {":foo": Element.ClientRef("foo"), "text-indigo-600": True, "text-6xl": True, "transition-transform": True, "duration-1500": True, "children": ["Hello World", !]}), Element("p", {":bar": Element.ClientRef("bar"), "text-cyan-600": True, "text-6xl": True, "transition-transform": True, "duration-1500": True, "children": ["Hello Fryweb", !]}), (Element("p", {":foobar": Element.ClientRef("foobar:a"), "children": ["foobar"]}) for i in range(3)), Element(Refed, {":refed": Element.ClientRef("refed"), ":refeds": Element.ClientRef("refeds:a")}), (Element(Refed, {":refeds": Element.ClientRef("refeds:a")}) for i in range(2))]})

if __name__ == '__main__':
    print(html(RefApp))
