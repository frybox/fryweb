from parsimonious import NodeVisitor, BadGrammar
from collections import defaultdict

import re

from fryhcs.fileiter import FileIter
from fryhcs.fry.grammar import grammar
from fryhcs.spec import is_valid_html_attribute
from fryhcs.element import class_attr_name

class BaseCollector():
    ignored_tags = ('head', 'title', 'meta', 'style', 'link', 'script', 'template')

    def __init__(self):
        self.fileiter = FileIter()
        self.attrs = defaultdict(set)
        self.classes = set()

    def add_glob(self, path, glob):
        self.fileiter.add_glob(path, glob)

    def add_file(self, file):
        self.fileiter.add_file(file)

    def collect_attrs(self):
        for file in self.fileiter.all_files():
            with file.open('r') as f:
                self.collect_from_content(f.read())

    def collect_from_content(self, data):
        pass

    def collect_kv(self, k, v):
        if not v: v = ""
        if len(v) > 1 and v[0] in "\"'":
            v = v[1:-1]
        vs = v.split()
        if not k or k == 'class':
            self.classes.update(vs)
        else:
            self.attrs[k].update(vs)

    def all_attrs(self):
        for cls in self.classes:
            yield '', cls
        for k, vs in self.attrs.items():
            if not vs:
                vs.add('')
            for v in vs:
                yield k, v


class RegexCollector(BaseCollector):
    tagname = r'([a-zA-Z0-9]+)'
    attrname = r"""[^\s"'>/=]+"""
    attrvalue = r"""'[^']*'|"[^"]*"|[^\s"'=><`]+"""
    attr = r"""[^"'>]*|"[^"]*"|'[^']*'"""

    #(?:xxx)表示不取值的group
    starttag_re = re.compile(f"<{tagname}((?:{attr})*)/?>")
    attr_re = re.compile(f"({attrname})(?:\s*=\s*({attrvalue}))?")

    def collect_from_content(self, data):
        for starttag in self.starttag_re.finditer(data):
            name = starttag.group(1)
            attrs = starttag.group(2)
            if name in self.ignored_tags:
                continue
            if not attrs:
                continue
            for attr in self.attr_re.finditer(attrs):
                self.collect_kv(attr.group(1), attr.group(2))


class CssVisitor(NodeVisitor):
    def __init__(self, collect_kv):
        self.collect_kv = collect_kv

    def collect_literal(self, css_literal):
        if css_literal:
            for css in css_literal.split():
                eq = css.find('=')
                if eq >= 0:
                    key = css[:eq]
                    value = css[eq+1:]
                else:
                    key = css
                    value = ''
                self.collect_kv(key, value)

    def generic_visit(self, node, children):
        return None

    def visit_single_quote(self, node, children):
        return node.text

    def visit_double_quote(self, node, children):
        return node.text

    def visit_py_simple_quote(self, node, children):
        # python中的简单字符串常量加入收集范围
        key = children[0]
        if not ' ' in key:
            key = key[1:-1]
            self.collect_kv(key, '')

    def visit_js_simple_quote(self, node, children):
        # js中的简单字符串常量加入收集范围
        key = children[0]
        if not ' ' in key:
            key = key[1:-1]
            self.collect_kv(key, '')

    def visit_fry_self_closing_element(self, node, children):
        _, name, attrs, _, _ = children
        if name[0].islower():
            for attr in attrs:
                if not isinstance(attr, tuple):
                    print(f'attr type {type(attr)}: {attr}')
                    raise BadGrammar
                if is_valid_html_attribute(name, attr[0]):
                    continue
                self.collect_kv(attr[0], attr[1])
        else:
            for attr in attrs:
                if not isinstance(attr, tuple):
                    print(f'attr type {type(attr)}: {attr}')
                    raise BadGrammar
                if attr[0] == '':
                    self.collect_kv('', attr[1])

    def visit_fry_void_element(self, node, children):
        _, name, attrs, _, _ = children
        for attr in attrs:
            if not isinstance(attr, tuple):
                print(f'attr type {type(attr)}: {attr}')
                raise BadGrammar
            # void_element必定是html元素
            if is_valid_html_attribute(name, attr[0]):
                continue
            self.collect_kv(attr[0], attr[1])

    def visit_fry_start_tag(self, node, children):
        _, start_name, attrs, _, _ = children
        if start_name[0].islower():
            for attr in attrs:
                if not isinstance(attr, tuple):
                    raise BadGrammar
                if is_valid_html_attribute(start_name, attr[0]):
                    continue
                self.collect_kv(attr[0], attr[1])
        else:
            for attr in attrs:
                if not isinstance(attr, tuple):
                    raise BadGrammar
                if attr[0] == '':
                    self.collect_kv('', attr[1])

    def visit_fry_element_name(self, node, children):
        return node.text

    def visit_fry_void_element_name(self, node, children):
        return node.text

    def visit_fry_attributes(self, node, children):
        return [ch for ch in children if ch]

    def visit_fry_spaced_attribute(self, node, children):
        _, attr = children
        return attr

    def visit_fry_attribute(self, node, children):
        return children[0]

    def visit_fry_kv_attribute(self, node, children):
        name, _, _, _, value = children
        if name == class_attr_name:
            # 将class名字设置为空字符串，is_valid_html_attribute返回false
            # 否则不会收集相关utilities。
            name = ''
        if isinstance(value, str):
            return (name, value)

    def visit_fry_novalue_attribute(self, node, children):
        name, _ = children
        return (name, '')

    def visit_fry_attribute_name(self, node, children):
        return node.text

    def visit_fry_attribute_value(self, node, children):
        return children[0]

    def visit_single_f_string(self, node, children):
        return node.text

    def visit_double_f_string(self, node, children):
        return node.text

class ParserCollector(BaseCollector):
    def collect_from_content(self, data):
        tree = grammar.parse(data)
        visitor = CssVisitor(self.collect_kv)
        visitor.visit(tree)

Collector = ParserCollector


if __name__ == '__main__':
    collector = Collector()
    collector.add_glob('test', '**/*.html')
    collector.collect_attrs()
    print("classes:")
    for cls in collector.classes:
        print("", cls)

    print("attrs:")
    for k,v in collector.attrs.items():
        print("", k, "\t\t", v)
