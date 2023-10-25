import inspect
from fryhcs.utils import static_url, component_name
from fryhcs.config import fryconfig
from fryhcs.css.style import CSS
import types

def escape(s):
    return s.replace('"', '\\"')


class RenderException(Exception):
    pass


def render_children(children, page):
    chs = []
    for ch in children:
        if isinstance(ch, (list, tuple, types.GeneratorType)):
            chs += render_children(ch, page)
        elif isinstance(ch, Element):
            chs.append(ch.render(page))
        else:
            chs.append(ch)
    return chs

def combine_style(style1, style2):
    if isinstance(style1, dict) and isinstance(style2, dict):
        result = {}
        result.update(style1)
        result.update(style2)
        return result
    elif isinstance(style1, dict) and isinstance(style2, str):
        result = ' '.join(f'{k}: {v};' for k,v in style1)
        return result + style2.strip()
    elif isinstance(style1, str) and isinstance(style2, dict):
        result = ' '.join(f'{k}: {v};' for k,v in style2)
        return result + style1.strip()
    elif isinstance(style1, str) and isinstance(style2, str):
        style1 = style1.strip()
        style2 = style2.strip()
        if len(style1) > 0 and style1[-1] != ';':
            style1 += ';'
        return style1 + style2


def convert_utilities(utilities):
    result = {}
    csses = [CSS(value=utility) for utility in utilities.split()]
    for css in csses:
        if not css.valid:
            raise RenderException(f"Invalid utility '{css.value}' in '@apply'")
        if css.wrappers or css.selector_template != css.default_selector_template:
            raise RenderException(f"Modifier is not allowed in '@apply': '{css.value}'")
        result.update(css.styles)
    return result


class ClientEmbed(object):
    def __init__(self, embed_id):
        self.embed_id = embed_id
        self.component = 0

    def hook(self, component):
        if self.component == 0:
            self.component = component

    def __str__(self):
        if self.component == 0:
            return str(self.embed_id)
        else:
            return f'{self.component}/{self.embed_id}'

component_attr_name = 'data-fryclass'
component_id_attr_name = 'data-fryid'
client_embed_attr_name = 'data-fryembed'
children_attr_name = 'children'
call_client_script_attr_name = 'call-client-script'
style_attr_name = 'style'
utility_attr_name = '$style'

class Element(object):

    def __init__(self, name, props={}, rendered=False):
        self.name = name
        self.props = props
        self.rendered = rendered

    def is_component(self):
        if self.rendered:
            return component_attr_name in self.props
        else:
            return inspect.isfunction(self.name) #or inspect.isclass(self.name)

    def hook_client_embed(self, component):
        def hook(v):
            if isinstance(v, ClientEmbed):
                v.hook(component)
            elif isinstance(v, (list, tuple)):
                for lv in v:
                    hook(lv)
            elif isinstance(v, dict):
                for lv in v.values():
                    hook(lv)
            elif isinstance(v, Element):
                hook(v.props)
        hook(self.props)

    def collect_client_embed(self, component):
        def collect(e):
            children = e.props.get(children_attr_name, [])
            for ch in children:
                if isinstance(ch, Element):
                    collect(ch)
            embeds = e.props.get(client_embed_attr_name, [])
            for key in list(e.props.keys()):
                if key in (client_embed_attr_name, children_attr_name):
                    continue
                value = e.props.get(key)
                if isinstance(value, ClientEmbed) and value.component == component:
                    if e.name == 'script':
                        value.embed_id = f'{value.embed_id}-object-{key}'
                    elif key[0] == '@':
                        value.embed_id = f'{value.embed_id}-event-{key[1:]}'
                    elif key.startswith('$$'):
                        value.embed_id = f'{value.embed_id}-attr-{key[2:]}'
                    elif key == '*':
                        value.embed_id = f'{value.embed_id}-text'
                    else:
                        raise RenderException(f"Invalid client embed key '{key}' for element '{e.name}'")
                    embeds.append(value)
                    e.props.pop(key)
            if embeds:
                e.props[client_embed_attr_name] = embeds
        collect(self)

    def render(self, page):
        """
        返回渲染后的元素。
        所有组件元素被渲染为基础元素（HTML元素），子元素列表中的子元素列表被摊平，属性值中不应再有元素
        """
        if self.rendered:
            return self

        if inspect.isfunction(self.name):
            # 渲染函数组件元素流程：
            # 1. 执行组件函数，返回未渲染的原始组件元素树
            #    元素树中的js嵌入值以ClientEmbed对象表示，元素树中
            #    的ClientEmbed对象有两类，一类是从组件函数参数中传进来
            #    的父组件js嵌入值，一类是新生成的本组件js嵌入值。
            #    父组件js嵌入值中有父组件实例唯一编号，本组件js嵌入值
            #    中(暂时)不带组件实例唯一编号。
            #    其中：
            #    * 元素树中html元素属性和文本中的js嵌入值都被移到
            #      所在元素的data-fryembed属性值列表中；
            #    * 元素树中子组件元素属性中的js嵌入值，将被当做
            #      props值传入子组件函数中
            result = self.name(self.props)
            if not isinstance(result, Element):
                raise RuntimeError(f"Function '{self.name.__name__}' should return Element")

            # 2. 生成页面内组件实例唯一编号
            #    组件函数每执行一次，返回该组件的一个实例。页面中
            #    每个组件实例都有一个页面内唯一编号。
            cnumber = page.add_component()

            # 3. 将组件实例唯一编号挂载到组件元素树的所有本组件生成的
            #    js嵌入值上，使每个js嵌入值具有页面内唯一标识，
            #    标识格式为：组件实例唯一编号/js嵌入值在组件内唯一编号
            result.hook_client_embed(cnumber)

            # 4. 从原始组件元素树根元素的属性中取出calljs属性值
            calljs = result.props.pop(call_client_script_attr_name, False)

            # 5. 原始组件元素树渲染为最终的html元素树，
            element = result.render(page)

            # 6. 此时已hook到组件实例的js嵌入值已挂载到html元素树上的合适
            #    位置，将这些js嵌入值收集到`client_embed_attr_name('data-fryembed')`属性上
            element.collect_client_embed(cnumber)
            
            # 7. 将组件名和组件实例ID附加到html元素树的树根元素上
            inner = element.props.get(component_attr_name, '')
            inner_id = element.props.get(component_id_attr_name, '')
            cname = component_name(self.name)
            element.props[component_attr_name] = f'{cname} {inner}' if inner else cname
            element.props[component_id_attr_name] = f'{cnumber} {inner_id}' if inner_id else str(cnumber)

            # 8. 如果当前组件存在js代码，将script脚本元素添加为树根元素的第一个子元素
            if calljs:
                uuid, args = calljs
                scriptprops = {
                    'src': static_url(fryconfig.js_url) + uuid + '.js',
                    #'defer': True,
                    component_id_attr_name: cnumber,
                    children_attr_name: [],
                }
                for k,v in args:
                    # 父组件实例传过来的js嵌入值
                    if isinstance(v, ClientEmbed):
                        scriptprops[k] = v
                    else:
                        scriptprops[f'data-{k}'] = v
                children = element.props[children_attr_name]
                children.insert(0, Element('script', scriptprops, True))
        elif isinstance(self.name, str):
            props = {}
            style = {} 
            for k in list(self.props.keys()):
                v = self.props[k]
                if k == children_attr_name:
                    props[k] = render_children(v, page)
                elif isinstance(v, Element):
                    props[k] = v.render(page)
                elif k == utility_attr_name:
                    if isinstance(v, (list, tuple, types.GeneratorType)):
                        v = ' '.join(v)
                    elif not isinstance(v, str):
                        raise RenderException(f"Invalid $style value: '{v}'")
                    style = combine_style(style, convert_utilities(v))
                elif k == style_attr_name:
                    style = combine_style(style, v)
                else:
                    props[k] = v
            if style:
                props[style_attr_name] = style
            element = Element(self.name, props, True)
        else:
            raise RenderException(f"invalid element name '{self.name}'")

        return element


    def __str__(self):
        if not self.rendered:
            return '<Element(not rendered)>'

        children = self.props.pop(children_attr_name, None)
        attrs = []
        for k, v in self.props.items():
            if isinstance(v, dict):
                values = []
                for k1, v1 in v.items():
                    values.append(f"{k1}: {v1};")
                value = ' '.join(values)
            elif isinstance(v, (list, tuple, types.GeneratorType)):
                value = ' '.join(str(x) for x in v)
            elif v is True:
                value = ''
            elif v is False:
                continue
            else:
                value = str(v)
            if value:
                attrs.append(f'{k}="{escape(value)}"')
            else:
                attrs.append(k)
        if attrs:
            attrs = ' ' + ' '.join(attrs)
        else:
            attrs = ''
        if children is None:
            return f'<{self.name}{attrs} />'
        else:
            children = ''.join(str(ch) for ch in children)
            return f'<{self.name}{attrs}>{children}</{self.name}>'


Element.ClientEmbed = ClientEmbed
