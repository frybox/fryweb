import inspect
from fryhcs.utils import static_url, component_name
from fryhcs.css.style import CSS
import types

def escape(s):
    return s.replace('"', '\\"')


class RenderException(Exception):
    pass


def render_children(children, page):
    chs = []
    for ch in children:
        if isinstance(ch, list): #tuple和GeneratorType都已转化为list
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
client_ref_attr_name = 'data-fryref'
client_refall_attr_name = 'data-fryrefall'
children_attr_name = 'children'
call_client_script_attr_name = 'call-client-script'
style_attr_name = 'style'
utility_attr_name = '$style'
ref_attr_name = 'ref'
ref_attr_name_prefix = 'ref:'
refall_attr_name = 'refall'
refall_attr_name_prefix = 'refall:'

class Element(object):

    def __init__(self, name, props={}, rendered=False):
        self.name = name
        self.props = props
        self.rendered = rendered
        self.cid = 0

    def is_component(self):
        if self.rendered:
            return component_attr_name in self.props
        else:
            return inspect.isfunction(self.name) #or inspect.isclass(self.name)

    def tolist(self):
        def convert(v):
            if isinstance(v, (tuple, types.GeneratorType)):
                return list(v)
            else:
                return v
        def handle(v):
            if isinstance(v, Element):
                v.props = {key: convert(value) for key, value in v.props.items()}
                handle(v.props)
            elif isinstance(v, dict):
                for key, value in v.items():
                    value = convert(value)
                    v[key] = value
                    handle(value)
            elif isinstance(v, list):
                for i, value in enumerate(v):
                    value = convert(value)
                    v[i] = value
                    handle(value)
        handle(self)

    def hook_client_embed(self, component):
        def hook(v):
            if isinstance(v, ClientEmbed):
                v.hook(component)
            elif isinstance(v, list): #tuple和GeneratorType都已转化为list
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
                    elif key.startswith(refall_attr_name_prefix):
                        name = key.split(':', 1)[1]
                        value.embed_id = f"{value.embed_id}-refall-{name}"
                    elif key.startswith(ref_attr_name_prefix):
                        name = key.split(':', 1)[1]
                        value.embed_id = f"{value.embed_id}-ref-{name}"
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
            # 1. 生成页面内组件实例唯一编号
            #    组件函数每执行一次，返回该组件的一个实例。页面中
            #    每个组件实例都有一个页面内唯一编号。
            cnumber = page.add_component()

            # 2. 将本组件上定义的给父组件js脚本用的ref/refall记录下来
            for key in list(self.props.keys()):
                if key.startswith(refall_attr_name_prefix):
                    name = key.split(':', 1)[1]
                    embed = self.props.pop(key)
                    pcid = embed.component
                    if pcid == 0:
                        raise RuntimeError("Invalid embed")
                    page.add_refall(pcid, name, cnumber)
                elif key.startswith(ref_attr_name_prefix):
                    name = key.split(':', 1)[1]
                    embed = self.props.pop(key)
                    pcid = embed.component
                    if pcid == 0:
                        raise RuntimeError("Invalid embed")
                    page.add_ref(pcid, name, cnumber)

            # 3. 执行组件函数，返回未渲染的原始组件元素树
            #    唯一不是合法python identifier的ref:jsname和refall:jsname已经在上一步
            #    删除，此时self.props的key应该都是合法的python identifier，可以
            #    **self.props用来给函数调用传参。
            #    元素树中的js嵌入值以ClientEmbed对象表示，元素树中
            #    的ClientEmbed对象只能是新生成的本组件js嵌入值。
            #    本组件js嵌入值中(暂时)不带组件实例唯一编号，通过下一步hook_client_embed
            #    将组件实例唯一编号附加到js嵌入值中。
            #    其中：
            #    * 元素树中html元素属性和文本中的js嵌入值都被移到
            #      所在元素的data-fryembed属性值列表中；
            #    * 元素树中子组件元素属性中的js嵌入值只有ref和refall，已经在
            #      上一步中处理，所以子组件元素属性中不存在js嵌入值
            result = self.name(**self.props)
            if not isinstance(result, Element):
                raise RuntimeError(f"Function '{self.name.__name__}' should return Element")

            # 4. 转化Generator/tuple为list，Generator只能遍历一次，后面会有多次的遍历
            #    tuple无法改变内部数据，也变为list
            result.tolist()

            # 5. 将组件实例唯一编号挂载到组件元素树的所有本组件生成的
            #    js嵌入值上，使每个js嵌入值具有页面内唯一标识，
            #    标识格式为：组件实例唯一编号/js嵌入值在组件内唯一编号
            result.hook_client_embed(cnumber)

            # 6. 从原始组件元素树根元素的属性中取出calljs属性值
            calljs = result.props.pop(call_client_script_attr_name, False)

            # 7. 原始组件元素树渲染为最终的html元素树，
            element = result.render(page)
            element.cid = cnumber

            # 8. 此时已hook到组件实例的js嵌入值已挂载到html元素树上的合适
            #    位置，将这些js嵌入值收集到`client_embed_attr_name('data-fryembed')`属性上
            element.collect_client_embed(cnumber)
            
            # 9. 将组件名和组件实例ID附加到html元素树树根元素下新增的第一个script元素上
            cname = component_name(self.name)
            scriptprops = {
                component_id_attr_name: cnumber,
                component_attr_name: cname,
                children_attr_name: [],
            }
            children = element.props[children_attr_name]
            # script是用来记录当前组件信息的，包括组件id，名字，以及后面可能的组件js参数
            children.insert(0, Element('script', scriptprops, True))

            # 10. 将子组件实例的引用附加到script上
            refs = page.child_refs(cnumber)
            if refs:
                refs = ' '.join(f'{name}-{ccid}' for name,ccid in refs.items())
                scriptprops[client_ref_attr_name] = refs
            refalls = page.child_refalls(cnumber)
            if refalls:
                refalls = [(name, '-'.join(str(ccid) for ccid in ccids)) for name, ccids in refalls.items()]
                refalls = ' '.join(f'{name}-{ccids}' for name, ccids in refalls)
                scriptprops[client_refall_attr_name] = refalls

            # 11. 若当前组件存在js代码，记录组件与脚本关系，然后将组件js参数加到script脚本上
            if calljs:
                uuid, args = calljs
                page.set_script(cnumber, uuid)
                for k,v in args:
                    if isinstance(v, ClientEmbed):
                        # 不支持父组件实例传过来的js嵌入值
                        #scriptprops[k] = v
                        raise RuntimeError(f"Js embed can't be used as script argument('{k}')")
                    else:
                        scriptprops[f'data-{k}'] = v
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
