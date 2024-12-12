# fry a237cff029ae33f326603f330ac5d78cf996fa19
from fryweb import Element

def RefApp():
    bar = 999
    return Element("div", {"call-client-script": ["pyvarref_RefApp", [("bar", bar)]], "children": [Element("p", {":foo": Element.ClientRef("foo"), "children": ["Hello World", !]})]})

if __name__ == '__main__':
    from fryweb import html
    print(html(RefApp))
