# fry d3f8e1f9d6d5b53b241fe559f71fb9362e01df93
from fryweb import Element
from random import randint

def A():
    x = {'id': 'great-a'}
    style = f'text-cyan-{randint(1, 9)*100} bg-#6667'
    #a = <span $style={style}>[](3)</span>
    a = Element("span", {"class": "bg-cyan-200 absolute", **(x), "style": (style), "children": [Element("span", {"*": Element.ClientEmbed(0), "children": [f"初{1}始{2}值"]})]})
    #a = <span $style={style}>[初始值](1)</span>
    return Element("span", {"call-client-script": ["nospaceattr_A", []], "children": [(a)]})

if __name__ == '__main__':
    from fryweb import render
    print(render(A))
