from parsimonious import NodeVisitor, BadGrammar
import sys
import re
import hashlib
from fryhcs.fry.grammar import grammar
from fryhcs.spec import is_valid_html_attribute
from fryhcs.css.style import CSS
from fryhcs.element import children_attr_name, call_client_script_attr_name, ref_attr_name, ref_attr_name_prefix

def escape(s):
    return s.replace('"', '\\"')

def quote_f_string(s):
    if not '"""' in s:
        quote = '"""'
    elif not "'''" in s:
        quote = "'''"
    else:
        raise BadGrammar(f"F-string '{s}' should not have both \"'''\" and '\"\"\"'")
    return f"f{quote}{s}{quote}"


class BaseGenerator(NodeVisitor):
    def __init__(self):
        self.client_embed_count = 0

    def inc_client_embed(self):
        count = self.client_embed_count
        self.client_embed_count = count + 1
        return count 

    def reset_client_embed(self):
        self.client_embed_count = 0

    def get_uuid(self, node):
        sha1 = hashlib.sha1()
        sha1.update(node.text.encode('utf-8'))
        return sha1.hexdigest()


#client_embed_attr_name = 'data-fryembed'

no_attr = 'no_attr'                   # ('no_attr', ...)
spread_attr = 'spread_attr'           # ('spread_attr', script): {script}
literal_attr = 'literal_attr'         # ('literal_attr', name, value): name="literal_value"
novalue_attr = 'novalue_attr'         # ('novalue_attr', name): name
py_attr = 'py_attr'                   # ('py_attr', name, pyscript): name={pyscript}
js_attr = 'js_attr'                   # ('js_attr', name, jscount): name=(jsscript)
jsop_attr = 'jsop_attr'               # ('jsop_attr', name, pyscript): name=({pyscript})
#2023.10.27 不再支持元素作为属性值，参考语法文件fry.ppeg说明
#element_attr = 'element_attr'         # ('element_attr', name, element): name=<element></element>
#2023.11.16 不在支持python嵌入后跟js嵌入
#pyjs_attr = 'pyjs_attr'               # ('pyjs_attr', name, pyscript, jscount): name={pyscript}(jsscript)
#pyjsop_attr = 'pyjsop_attr'           # ('pyjsop_attr', name, pyscript, pyscript): name={pyscript1}({pyscript2})
fsjs_attr = 'fsjs_attr'               # ('fsjs_attr', name, value, jscount): name=[value](jsscript)
fsjsop_attr = 'fsjsop_attr'           # ('fsjsop_attr', name, value, value): name=[value]({pyscript})
children_attr = 'children_attr'       # ('children_attr', [children])
jstext_attr = 'jstext_attr'           # ('jstext_attr', jscount)
jsoptext_attr = 'jsoptext_attr'       # ('jsoptext_attr', value)
call_client_attr = 'call_client_attr' # ('call_client_attr', uuid, args)

def concat_kv(attrs):
    ats = []
    for attr in attrs:
        if isinstance(attr, (list, tuple)):
            atype = attr[0]
            if atype == spread_attr:
                ats.append(attr[1])
            elif atype == literal_attr:
                _, name, value = attr
                ats.append(f'"{name}": {value}')
            elif atype == novalue_attr:
                name = attr[1]
                ats.append(f'"{name}": ""')
            elif atype == py_attr:
                _, name, value = attr
                ats.append(f'"{name}": {value}')
            elif atype == js_attr:
                _, name, jscount = attr
                ats.append(f'"{name}": Element.ClientEmbed({jscount})')
            elif atype == jsop_attr:
                _, name, value = attr
                ats.append(f'"{name}": {value}')
            #elif atype == element_attr:
            #    _, name, value = attr
            #    ats.append(f'"{name}": {value}')
            #elif atype == pyjs_attr:
            #    _, name, value, jscount = attr
            #    ats.append(f'"{name}": {value}')
            #    ats.append(f'"$${name}": Element.ClientEmbed({jscount})')
            #elif atype == pyjsop_attr:
            #    _, name, value, jsvalue = attr
            #    ats.append(f'"{name}": {value}')
            #    ats.append(f'"$${name}": {jsvalue}')
            elif atype == fsjs_attr:
                _, name, value, jscount = attr
                ats.append(f'"{name}": {value}')
                ats.append(f'"$${name}": Element.ClientEmbed({jscount})')
            elif atype == fsjsop_attr:
                _, name, value, jsvalue = attr
                ats.append(f'"{name}": {value}')
                ats.append(f'"$${name}": {jsvalue}')
            elif atype == children_attr:
                ats.append(f'"{children_attr_name}": [{", ".join(attr[1])}]')
            elif atype == jstext_attr:
                _, jscount = attr
                ats.append(f'"*": Element.ClientEmbed({jscount})')
            elif atype == jsoptext_attr:
                _, jsvalue = attr
                ats.append(f'"*": {jsvalue}')
            elif atype == call_client_attr:
                _, uuid, args = attr
                args = ', '.join(f'("{k}", {v})' for k,v in args)
                ats.append(f'"{call_client_script_attr_name}": ["{uuid}", [{args}]]')
            elif atype == no_attr:
                pass
            else:
                raise BadGrammar(f"Invalid attribute: {attr}")
        else:
            raise BadGrammar(f"Invalid attr: {attr}")
    return ats

# 检查并预处理html基本元素的属性
#
#   html基本元素是符合html规范的元素，支持无属性值属性、有属性值属性、事件处理器属性，属性有如下几种：
#   * `name`                               : 无值属性，如果是符合html规范的属性，正常传给浏览器引擎，否则放到class中
#                                            服务端：class中的值，或无值属性
#                                            浏览器：class中的值，或无值属性
#   * `name="literal_value"`               : 符合html规范的属性在客户端传给浏览器引擎，否则放到css中
#                                            服务端：class中的值，或正常html元素属性
#                                            浏览器：class中的值，或正常html元素属性
#   * `name='literal_value'`               : 符合html规范的属性在客户端传给浏览器引擎，否则放到css中
#                                            服务端：class中的值，或正常html元素属性
#                                            浏览器：class中的值，或正常html元素属性
#   * `name=(js_value)`                    : 这种格式目前只支持name=ref，js_value是一个js变量名，用于将
#                                            当前元素赋值给一个js变量
#   * `@event=(js_handler)`                : 本组件的js事件处理函数
#   * `@event=({jsop_handler})`            : 父组件的js事件处理函数
#                                            服务端：ClientEmbed对象
#                                            浏览器：data-fry-script一项
#   * `@event={py_value}`                  : ClientEmbed类型的python值，父组件的事件处理函数
#                                            服务端：data-fry-script一项
#                                            浏览器：data-fry-script一项
#   * `$name={py_value}`                   : python值在服务端渲染为常量赋值给属性name，传给浏览器引擎
#                                            目前支持的name只有"style"($style), 用于使用utility指定元素内置style，
#   * `$name='literal_value'`              : utility列表值在服务端转化为CSS，传给浏览器引擎
#   * `$name="literal_value"`              : utility列表值在服务端转化为CSS，传给浏览器引擎
#                                            目前支持的name只有"class"($class), 用于向CSSGenerator传递一些动态生成的、
#                                            运行期间才能看到的utility, 实际渲染中$class被忽略
#                                            注：$class不会出现在这里，在解析过程中就过滤掉了(see `visit_fry_kv_attribute`)
#   * `name={py_value}`                    : python值在服务端渲染为常量传给浏览器引擎，不可以为ClientEmbed
#                                            服务端：`name=py_value`，python数据值
#                                            浏览器：`name="py_value"`，字符串值，如果是ClientEmbed时生成data-fry-script一项
# 2023.11.16: 如下两种情况不再支持：
#   * `name={py_value}(js_value)`          : python值，客户端js修改
#   * `name={py_value}({jsop_value})`      : python值，客户端父组件js修改
#                                            服务端：`name=py_value`，python数据值
#                                            浏览器：`name="py_value"`，字符串值，同时新增data-fry-script一项
#   * `name=[literal_value](js_value)`     : 常量字符串，客户端js修改
#   * `name=[literal_value]({jsop_value})` : 常量字符串，客户端父组件js修改
#                                            服务端：`name=literal_value`，python数据值
#                                            浏览器：`name="literal_value"`，字符串值，同时新增data-fry-script一项
#   * `{*python_list}`                     : python列表值，服务端渲染为常量传给浏览器引擎
#   * `{**python_dict}`                    : python字典值，服务端渲染为常量传给浏览器引擎
def check_html_element(name, attrs):
    classes = []
    class_attr = None
    for attr in attrs:
        atype = attr[0]
        if atype not in (novalue_attr, literal_attr, js_attr, py_attr, fsjs_attr, fsjsop_attr, spread_attr):
            raise BadGrammar(f"Invalid attribute type '{atype}' in html element '{name}'")
        if attr[1][0] == '@' and atype not in (js_attr, py_attr):
            raise BadGrammar(f"Invalid attribute type '{atype}' for event handler '{attr[1]}' in html element '{name}'")
        if attr[1][0] == '$':
            if attr[1] not in ('$style',):
                raise BadGrammar("unsupported attribute name: '{attr[1]}'")
            if attr[1] == '$style' and atype != py_attr:
                raise BadGrammar(f"invalid attribute type '{atype}' for '$style' in html element '{name}': '{py_attr}' needed.")
        if atype == js_attr:
            if attr[1][0] != '@' and not attr[1].startswith(ref_attr_name_prefix):
                raise BadGrammar(f"js_attr type can only be specified for event handler or ref, not '{attr[1]}'")
            attr[0] = py_attr
            attr[2] = f'Element.ClientEmbed({attr[2]})'
        if atype == novalue_attr:
            key = attr[1]
            value = ''
        elif atype == literal_attr:
            _, key, value = attr
            if value[0] in '\'"':
                value = value[1:-1]
        else:
            continue
        if key == 'class' and atype == literal_attr:
            class_attr = attr
            continue
        if is_valid_html_attribute(name, key):
            continue
        values = value.split()
        if not values:
            values = ['']
        classes.extend(CSS(key, value).to_class() for value in values) 
        attr[0] = no_attr
    if classes:
        classes = ' '.join(classes)
        if not class_attr:
            class_attr = [literal_attr, 'class', '""']
            attrs.append(class_attr)
        value = class_attr[2]
        if value[0] in '\'"':
            value = value[1:-1]
        if value:
            class_attr[2] = f'"{value} {classes}"'
        else:
            class_attr[2] = f'"{classes}"'


# 检查并预处理组件元素的属性
#
#   组件元素以大写字母开头的名字作为元素名，元素名代表一个组件函数。
#   组件元素的属性作为python参数列表传给组件函数，所以组件元素只支持如下几种格式的属性：
#   * `name="literal_value"`: 常量字符串在服务端传给子组件
#                             服务端：常量字符串
#                             浏览器：不可见
#   * `name='literal_value'`: 常量字符串在服务端传给子组件
#                             服务端：常量字符串
#                             浏览器：不可见
#   * `name={py_value}`     : python值在服务端运行时传给子组件，可以是各种类型数据，包括ClientEmbed
#                             服务端：python数据
#                             浏览器：不可见
#   * `name=(js_value)`     : 本组件js值在客户端运行时传给子组件
#   * `name=({jsop_value})` : 父组件js值在客户端运行时传给子组件
#                             服务端：ClientEmbed对象
#                             浏览器：不可见
#   * `{*python_list}`      : python列表值
#                             服务端：传递给python组件函数的props参数的一部分
#                             浏览器：不可见
#   * `{**python_dict}`     : python字典值
#                             服务端：传递给python组件函数的props参数的一部分
#                             浏览器：不可见
def check_component_element(name, attrs):
    for attr in attrs:
        atype = attr[0]
        if atype not in (spread_attr, literal_attr, py_attr, js_attr, jsop_attr):
            raise BadGrammar(f"Invalid attr '{atype}': Component element can only have spread_attr, literal_attr, py_attr, js_attr, jsop_attr")
        if atype != spread_attr and not attr[1].isidentifier():
            raise BadGrammar(f"Invalid attibute name '{attr[1]}' on Component element '{name}', identifier needed.")
        if atype == js_attr:
            # TODO 检查如下设置是否合理
            if attr[1].startswith(ref_attr_name_prefix):
                raise BadGrammar(f"Can't ref to component element yet now, only DOM element can be REFed.")
            attr[0] = py_attr
            attr[2] = f'Element.ClientEmbed({attr[2]})'

class PyGenerator(BaseGenerator):
    def generate(self, tree):
        self.web_component_script = False
        self.client_script_args = {}
        self.refs = set()
        self.reset_client_embed()
        return self.visit(tree)

    def generic_visit(self, node, children):
        return children or node

    def visit_fry_script(self, node, children):
        return ''.join(str(ch) for ch in children)

    def visit_inner_fry_script(self, node, children):
        return ''.join(str(ch) for ch in children)

    def visit_fry_script_item(self, node, children):
        return children[0]

    def visit_inner_fry_script_item(self, node, children):
        item = children[0]
        if isinstance(item, tuple):
            if item[0] == 'element':
                return item[1]
            else:
                raise BadGrammar
        return item 

    def visit_py_comment(self, node, children):
        return node.text

    def visit_inner_fry_brace(self, node, children):
        _, script, _ = children
        # inner_brace是正常的python脚本，需要原样输出
        return '{' + script + '}'

    def visit_fry_embed(self, node, children):
        _, script, _ = children
        # embed都是赋值表达式，可以直接加上小括号
        return ('fry_embed', '(' + script + ')')

    def visit_triple_single_quote(self, node, children):
        return node.text

    def visit_triple_double_quote(self, node, children):
        return node.text

    def visit_single_quote(self, node, children):
        return node.text

    def visit_double_quote(self, node, children):
        return node.text

    def visit_py_simple_quote(self, node, children):
        return children[0]

    def visit_fry_simple_quote(self, node, children):
        return children[0]

    def visit_js_simple_quote(self, node, children):
        return children[0]

    def visit_less_than_char(self, node, children):
        return '<'

    def visit_py_normal_code(self, node, children):
        return node.text

    def visit_inner_py_normal_code(self, node, children):
        return node.text

    def visit_fry_element_with_web_script(self, node, children):
        element, _webscript = children
        name, attrs = element
        if self.web_component_script:
            uuid = self.get_uuid(node)
            args = [(k,v) for k,v in self.client_script_args.items()]
            attrs.insert(0, [call_client_attr, uuid, args])
        self.web_component_script = False
        self.client_script_args = {}
        self.refs = set()
        self.reset_client_embed()
        attrs = concat_kv(attrs)
        return f'Element({name}, {{{", ".join(attrs)}}})'

    def visit_fry_root_element(self, node, children):
        name, attrs = children[0]
        if name == 'script':
            raise BadGrammar("'script' can't be used as the normal element name") 
        return name, attrs

    def visit_fry_element(self, node, children):
        name, attrs = children[0]
        if name == 'script':
            raise BadGrammar("'script' can't be used as the normal element name") 
        attrs = concat_kv(attrs)
        return ('element', f'Element({name}, {{{", ".join(attrs)}}})')

    def visit_fry_fragment(self, node, children):
        _, fry_children, _ = children
        return ('"div"', [[children_attr, fry_children]])

    def visit_fry_self_closing_element(self, node, children):
        _, name, attrs, _, _ = children
        if not name:
            raise BadGrammar
        if name[0].islower():
            check_html_element(name, attrs)
            name = f'"{name}"'
        else:
            check_component_element(name, attrs)
        # self closing元素不能有children属性，否则组件函数的参数会出错。
        #attrs.append([children_attr,[]])
        return (name, attrs)

    def visit_fry_paired_element(self, node, children):
        start, fry_children, end = children
        start_name, attrs = start
        end_name = end
        if start_name != end_name:
            raise BadGrammar(f'start_name "{start_name}" is not the same with end_name "{end_name}"')
        name = start_name
        if not name:
            raise BadGrammar
        elif name[0].islower():
            check_html_element(name, attrs)
            name = f'"{name}"'
        else:
            check_component_element(name, attrs)

        attrs.append([children_attr, fry_children])

        return (name, attrs)

    def visit_fry_start_tag(self, node, children):
        _, start_name, attrs, _, _ = children
        return start_name, attrs

    def visit_fry_end_tag(self, node, children):
        _, name, _, _ = children
        return name

    def visit_fry_element_name(self, node, children):
        return node.text

    def visit_space(self, node, children):
        return node.text

    def visit_maybe_space(self, node, children):
        return node.text

    def visit_fry_attributes(self, node, children):
        # 过滤掉$class="xxx"
        return [ch for ch in children if ch]

    def visit_fry_spaced_attribute(self, node, children):
        space, attr = children
        if not space and attr:
            # 元素属性前最好有空格
            print(f"Warning: attribute {attr} should be prefixed with white space.")
        return attr

    def visit_fry_attribute(self, node, children):
        return children[0]

    def visit_fry_embed_spread_attribute(self, node, children):
        _lbrace, _, stars, _, script, _rbrace = children
        if stars.text == '*':
            return [spread_attr, "**{ key: True for key in (" + script + ")}"]
        return [spread_attr, '**(' + script + ')']

    #def visit_fry_client_embed_attribute(self, node, children):
    #    value, _, _css_literal = children
    #    _name, literal, client_embed = value
    #    kvs = [(name, '""') for name in literal.split()]
    #    count = self.inc_client_embed()
    #    return (client_embed_attr_name, kvs, str(count))

    #def visit_fry_event_attribute(self, node, children):
    #    _at, _identifier, _, _equal, _, _client_embed = children
    #    count = self.inc_client_embed()
    #    return (client_embed_attr_name, [], str(count))

    def visit_fry_kv_attribute(self, node, children):
        name, _, _, _, value = children
        if name == '$class':
            if not isinstance(value, str):
                raise BadGrammar("'$class' can only have literal value")
            return None 
        if isinstance(value, str):
            return [literal_attr, name, value]
        elif isinstance(value, tuple):
            if value[0] == 'joint_embed':
                _, quoted_literal, client_embed = value
                if client_embed[0] == 'local_js_embed':
                    count = self.inc_client_embed()
                    return [fsjs_attr, name, quoted_literal, str(count)]
                elif client_embed[0] == 'jsop_embed':
                    return [fsjsop_attr, name, quoted_literal, client_embed[1]]
                else:
                    raise BadGrammar
            #elif value[0] == 'fry_js_embed':
            #    _, embed, client_embed = value
            #    if client_embed[0] == 'local_js_embed':
            #        count = self.inc_client_embed()
            #        return [pyjs_attr, name, embed, str(count)]
            #    elif client_embed[0] == 'jsop_embed':
            #        return [pyjsop_attr, name, embed, client_embed[1]]
            #    else:
            #        raise BadGrammar
            elif value[0] == 'fry_embed':
                _, embed = value
                return [py_attr, name, embed]
            elif value[0] == 'local_js_embed':
                count = self.inc_client_embed()
                if name == ref_attr_name:
                    # 将js变量名编码到ref name中
                    name = value[1].strip()
                    if not name.isidentifier():
                        raise BadGrammar(f"Ref name '{name}' is not a valid identifier")
                    if name in self.refs:
                        raise BadGrammar(f"Duplicated ref name '{name}'")
                    self.refs.add(name)
                    name = ref_attr_name_prefix + name
                return [js_attr, name, str(count)]
            elif value[0] == 'jsop_embed':
                return [jsop_attr, name, value[1]]
            #elif value[0] == 'element':
            #    return [element_attr, name, value[1]]
            else:
                raise BadGrammar(f'Invalid attribute value: {value[0]}')
        else:
            raise BadGrammar(f'Invalid attribute value: {value}')

    def visit_fry_novalue_attribute(self, node, children):
        name, _ = children
        return [novalue_attr, name]

    def visit_fry_attribute_name(self, node, children):
        return node.text

    def visit_fry_attribute_value(self, node, children):
        return children[0]

    #def visit_fry_attr_value_embed(self, node, children):
    #    embed, _, client_embed, _, _css_literal = children
    #    return ('embed_value', embed, client_embed)

    #def visit_fry_attr_value_client_embed(self, node, children):
    #    value, _, _css_literal = children
    #    return value #('client_embed', literal, client_embed)

    #def visit_fry_css_literal(self, node, children):
    #    _colon, _, value = children
    #    return value

    #def visit_maybe_css_literal(self, node, children):
    #    if not children:
    #        return ''
    #    return children[0]

    def visit_fry_children(self, node, children):
        return [ch for ch in children if ch]

    def visit_fry_child(self, node, children):
        frychild = children[0]
        if isinstance(frychild, str):
            return frychild
        elif isinstance(frychild, tuple):
            #if frychild[0] == 'fry_js_embed':
            #    _, embed, client_embed = frychild
            #    if client_embed[0] == 'local_js_embed':
            #        attr = jstext_attr
            #        value = str(self.inc_client_embed())
            #    elif client_embed[0] == 'jsop_embed':
            #        attr = jsoptext_attr
            #        value = client_embed[1]
            #    else:
            #        raise BadGrammar
            #    attrs = [[attr, value],
            #             [children_attr, [embed]]]
            #    attrs = concat_kv(attrs)
            #    return f'Element("span", {{{", ".join(attrs)}}})'
            #elif frychild[0] == 'fry_embed':
            if frychild[0] == 'fry_embed':
                _, embed = frychild
                return embed
            elif frychild[0] == 'joint_embed':
                _, quoted_literal, client_embed = frychild
                if client_embed[0] == 'local_js_embed':
                    attr = jstext_attr
                    value = str(self.inc_client_embed())
                elif client_embed[0] == 'jsop_embed':
                    attr = jsoptext_attr
                    value = client_embed[1]
                else:
                    raise BadGrammar
                attrs = [[attr, value],
                         [children_attr, [quoted_literal]]]
                attrs = concat_kv(attrs)
                return f'Element("span", {{{", ".join(attrs)}}})'
            elif frychild[0] == 'element':
                return frychild[1]
        else:
            raise BadGrammar(f'Invalid fry_child "{frychild}"')

    #def visit_fry_js_embed(self, node, children):
    #    fry_embed, _, js_embed = children
    #    _name, fry = fry_embed
    #    return ('fry_js_embed', fry, js_embed)

    def visit_joint_embed(self, node, children):
        _l, quoted_literal, _r, _, js_embed = children
        return ('joint_embed', quoted_literal, js_embed)

    def visit_f_string(self, node, children):
        return quote_f_string(node.text)

    def visit_fry_text(self, node, children):
        value = re.sub(r'(\s+)', lambda m: ' ', node.text).strip()
        if not value or value == ' ':
            return ''
        return f'"{escape(value)}"'

    def visit_no_embed_char(self, node, children):
        return node.text

    # 脚本元素的元素名为script，代表了一个组件对应的js脚本，一个组件最多有一个脚本元素。
    # 脚本元素的属性作为js参数列表传给脚本代码，并且脚本代码需要在编译期生成，属性名需要在编译期可见，
    # 不能依赖python运行期的信息，所以脚本元素只支持如下几种格式的属性：
    # * `name`                : 无值属性，主要用于定义一个局部变量，用来绑定DOM元素
    # * `name="literal_value"`: 常量字符串在客户端传给js脚本
    #                           服务端：`data-name="literal_value"`
    #                           浏览器：`data-name="literal_value"`
    # * `name='literal_value'`: 常量字符串在客户端传给js脚本
    #                           服务端：`data-name='literal_value'`
    #                           浏览器：`data-name="literal_value"`
    # * `name={py_value}`     : python值作为字符串在客户端运行时传给js脚本，在客户端是一个常量字符串
    #                           服务端：`data-name=py_value`，python数据值
    #                           浏览器：`data-name="py_value"`，字符串值。
    # * `name=({py_value})`   : ClientEmbed值在客户端运行时传给本组件js脚本，是父组件的js值
    #                           服务端：`data-fryembed=[ClientEmbed]`，ClientEmbed值
    #                           浏览器：`data-fryembed="4/3-object-foo"`，父组件js值
    # name不能以'fry'开头
    def visit_web_script(self, node, children):
        self.web_component_script = True
        _, _sep, _, _begin, attributes, _, _lessthan, _script, _end = children
        for attr in attributes:
            # TODO spread_attr是不是也可以用在这里？
            if attr[0] not in (novalue_attr, literal_attr, py_attr, jsop_attr):
                raise BadGrammar("script attributes can only be novalue_attr, literal_attr, py_attr or jsop_attr")
            name = attr[1]
            if not name.isidentifier():
                raise BadGrammar(f"Script argument name '{name}' is not valid identifier.")
            if attr[0] == novalue_attr:
                if name not in self.refs:
                    raise BadGrammar(f"Script argument name '{name}' is not a valid REF.")
                continue
            atype, k, v = attr
            if k.startswith('fry'):
                raise BadGrammar(f"Prefix 'fry' is reserved, <script> attribute name can't be started with 'fry'")
            self.client_script_args[k] = v
        return ''

    def visit_html_comment(self, node, children):
        return ''

    def visit_js_embed(self, node, children):
        self.web_component_script = True
        return children[0]

    def visit_local_js_embed(self, node, children):
        # 返回js script内容，在ref DOM元素时有用
        return ('local_js_embed', node.text[1:-1])

    def visit_jsop_embed(self, node, children):
        _l, script, _r = children
        return ('jsop_embed', script)


def fry_to_py(source):
    """
    fry文件内容转成py文件内容
    """
    tree = grammar.parse(source)
    generator = PyGenerator()
    return generator.generate(tree)
