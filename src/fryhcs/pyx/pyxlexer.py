from pygments.lexer import bygroups, default, include, inherit
from pygments.lexers.python import PythonLexer
from pygments.lexers.javascript import JavascriptLexer
from pygments.token import Name, Operator, Punctuation, String, Text, Whitespace, Comment

class PyxLexer(PythonLexer):
    name = 'Pyx'
    aliases = ['pyx']
    filenames = ['*.pyx']
    mimetypes = ['text/pyx']

    tokens = {
        'root': [
            include("pyx"),
            inherit,
        ],
        'pyx': [
            (r'<>', Punctuation, 'fragment_children'),
            (r'(<)(area|base|br|col|embed|hr|img|input|link|meta|source|track|wbr)\b', 
              (Punctuation, Name), 'void_element'),
        ],
        'fragment_children': [
            (r'</>', Punctuation, '#pop'),
            include('children'),
        ],
        'void_element': [
            (r'\s*/?>', Punctuation, '#pop'),
            include('attributes'),
        ],
        'children': [
        ],
    }


from parsimonious import NodeVisitor, BadGrammar
from fryhcs.pyx.grammar import grammar

def merge(children):
    result = []
    for child in children:
        if isinstance(child, list):
            new = merge(child)
            if result and new and result[-1][0] == new[0][0]:
                result[-1] = (new[0][0], result[-1][1]+new[0][1])
                new = new[1:]
            result += new
        elif isinstance(child, tuple):
            if len(child[1]) == 0:
                continue
            if result and result[-1][0] == child[0]:
                result[-1] = (child[0], result[-1][1]+child[1])
            else:
                result.append(child)
        else:
            raise BadGrammar(f"invalid: |{child}|, {type(child)}")
    return result

def an(text):
    return (Name.Attribute, text)

def en(text):
    if text[0].islower():
        return (Name.HtmlElement, text)
    else:
        return (Name.ComponentElement, text)

def n(text):
    return (Name, text)

def o(text):
    return (Operator, text)

def p(text):
    return (Punctuation, text)

def ep(text):
    return (Punctuation.ElementPunctuation, text)

def sep(text):
    return (Punctuation.ServerEmbedPunctuation, text)

def cep(text):
    return (Punctuation.ClientEmbedPunctuation, text)

def s(text):
    return (String, text)

def w(text):
    return (Whitespace, text)

def t(text):
    return (Text.HtmlText, text)

def py(text):
    return ('python', text)

def js(text):
    return ('javascript', text)

def fs(text):
    return ('fstring', text)

class PyxVisitor(NodeVisitor):
    def generic_visit(self, node, children):
        return children or node.text

    def visit_script(self, node, children):
        return merge(children)

    def visit_inner_script(self, node, children):
        return children

    def visit_script_item(self, node, children):
        return children[0]

    def visit_inner_script_item(self, node, children):
        return children[0]

    def visit_comment(self, node, children):
        return py(node.text)

    def visit_inner_brace(self, node, children):
        _l, script, _r = children
        return [py('{'), script, py('}')]

    def visit_embed(self, node, children):
        _l, script, _r = children
        return [sep('{'), script, sep('}')]
        
    def visit_triple_single_quote(self, node, children):
        return py(node.text)

    def visit_triple_double_quote(self, node, children):
        return py(node.text)

    def visit_single_quote(self, node, children):
        return node.text

    def visit_double_quote(self, node, children):
        return node.text

    def visit_py_simple_quote(self, node, children):
        return py(children[0])

    def visit_pyx_simple_quote(self, node, children):
        return s(children[0])

    def visit_js_simple_quote(self, node, children):
        return js(children[0])

    def visit_less_than_char(self, node, children):
        return py('<')

    def visit_normal_code(self, node, children):
        return py(node.text)

    def visit_inner_normal_code(self, node, children):
        return py(node.text)

    def visit_pyx_element_with_web_script(self, node, children):
        return children

    def visit_pyx_root_element(self, node, children):
        return children[0]

    def visit_pyx_element(self, node, children):
        return children[0]

    def visit_pyx_fragment(self, node, children):
        l, chs, r = children
        return [ep(l), chs, ep(r)]

    def visit_pyx_self_closing_element(self, node, children):
        l, name, attrs, s, r = children
        return [ep(l), name, attrs, w(s), ep(r)]

    def visit_pyx_paired_element(self, node, children):
        return children

    def visit_pyx_start_tag(self, node, children):
        l, name, attrs, s, r = children
        return [ep(l), name, attrs, w(s), ep(r)]

    def visit_pyx_end_tag(self, node, children):
        l, name, s, r = children
        return [ep(l), name, w(s), ep(r)]

    def visit_pyx_element_name(self, node, children):
        return en(node.text)

    def visit_space(self, node, children):
        return node.text

    def visit_maybe_space(self, node, children):
        return node.text

    def visit_pyx_attributes(self, node, children):
        return children

    def visit_pyx_spaced_attribute(self, node, children):
        s, attr = children
        return [w(s), attr]

    def visit_pyx_attribute(self, node, children):
        return children[0]

    def visit_pyx_embed_spread_attribute(self, node, children):
        l, s1, m, s2, script, r = children
        return [sep(l), py(s1), py(m), py(s2), script, sep(r)]

    def visit_pyx_kv_attribute(self, node, children):
        name, s1, e, s2, value = children
        return [name, w(s1), o(e), w(s2), value]

    def visit_pyx_novalue_attribute(self, node, children):
        return children[0]

    def visit_pyx_attribute_name(self, node, children):
        return an(node.text)

    def visit_pyx_attribute_value(self, node, children):
        return children[0]

    def visit_pyx_children(self, node, children):
        return children

    def visit_pyx_child(self, node, children):
        return children[0]

    def visit_embed_value(self, node, children):
        embed, s, client_embed = children
        return [embed, w(s), client_embed]

    def visit_client_embed_value(self, node, children):
        lb, fs, rb, s, client_embed = children
        return [sep(lb), fs, sep(rb), w(s), client_embed]
        
    def visit_f_string(self, node, children):
        return fs(node.text)

    def visit_pyx_text(self, node, children):
        return t(node.text)

    def visit_no_embed_char(self, node, children):
        return t(node.text)

    def visit_maybe_web_script(self, node, children):
        return children

    def visit_web_script(self, node, children):
        s1, comma, s2, ls, attrs, s3, r1, script, r2 = children
        return [w(s1), p(comma), w(s2), ep('<'), en('script'), attrs, w(s3), ep(r1), script, ep('</'), en('script'), ep('>')]

    def visit_html_comment(self, node, children):
        return (Comment.HtmlComment, node.text)

    def visit_client_script(self, node, children):
        return js(node.text)

    def visit_maybe_client_embed(self, node, children):
        return children

    def visit_client_embed(self, node, children):
        return children[0]

    def visit_js_client_embed(self, node, children):
        l, script, r = children
        return [cep(l), script, cep(r)]

    def visit_jsop_client_embed(self, node, children):
        l, script, r = children
        return [cep('('), sep('{'), script, sep('}'), cep(')')]


def classify(source):
    tree = grammar.parse(source)
    visitor = PyxVisitor()
    return visitor.visit(tree)

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        with open(sys.argv[1], 'r') as f:
            data = f.read()
        for d in classify(data):
            print(d)
