# fry ac5ecd75b828097a4a375df4cbcd3103f6d9e5fa
from fryweb import Element
from random import randint

def A():
    style = f'text-cyan-{randint(1, 9)*100} bg-#6667'
    #a = <span $style={style}>[](3)</span>
    a = Element("span", {"class": "bg-cyan-200 absolute", "children": [Element("span", {"*": Element.ClientEmbed(0), "children": [f"初{1}始{2}值"]})]})
    #a = <span $style={style}>[初始值](1)</span>
    return Element("div", {"call-client-script": ["embedded_A", []], "children": [(a)]})

if __name__ == '__main__':
    from fryweb import render
    print(render(A))
