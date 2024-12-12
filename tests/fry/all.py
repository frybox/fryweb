# fry 715ac5c7615ece98d4946eed732de17b8915e938
from fryweb import Element

# 这是一个fy样例

# fy是一个内嵌html语法的python语法扩展，通过fryweb将fy语法转化为python语法
# fy内嵌html的方式如下：
# from fryweb.html import Element
# my_element = <div class="my-element">这是我的div</div>
# another_element = (
#   <div mt-8 hidden>
#     这是一个支持<span text-red>fryweb</span>语法的div
#   </div>)
# 在注释和字符串中的html不会被fryweb转化。

def FunctionComponent(value, **props):
    print(f"FunctionComponent: '{props}'")
    # 可以直接将html赋值给变量
    content1 = Element("span", {"text-cyan-500": True, "hover:text": "cyan-400", "hover:container": True, "dark": "text-cyan-600", "children": ["你好"]})

    # 多行html赋值的时候可以加括号:
    content2 = (
      Element("span", {"class": "content1", "children": ["你好：", (content1)]}))

    # 也可以不加括号，但等号不能作为一行的最后一个字符，等好后需要在同行有元素：
    content3 = Element("div", {"id": 'content3', "children": ["你好:", Element("span", {"children": ["Mr. bad", !]})]})
    # 上面例子也可看出，属性值可以是单引号括起来


    # 字符串中的html不受影响
    content4 = "这是不受影响的html：<span text-cyan-500>'你好'</span>"
    content5 = '这是不受影响的html：<span text-cyan-500>"你好"</span>'
    content6 = '''
         这是不受影响的html：
         <span text-cyan-500>
           "你好"
         </span>
         '''
    content7 = """
         这是不受影响的html：
         <span text-cyan-500>
           "你好"
         </span>
         """

    # 2023.10.27: 属性值不支持元素了
    # 属性值也可以是元素，但只有组件元素的属性值可以是元素，html元素的属性值不行
    content8 = """<FunctionComponent2 base=<span class="hello">hello</span>>
                属性值是html元素的div
               </FunctionComponent2>"""

    # self-closing的变量
    br1 = Element("br", {})
    br2 = Element("br", {})

    # html fragment
    fragment1 = (
      Element("div", {"children": [Element("p", {"text-black": True, "children": ["你好"]}), Element("div", {"float": "left", "children": ["你也", Element("span", {"class": 'good', "children": ["好"]})]}), "over: &quot;ok&quot;, &#x27;good&#x27;"]})
    )
    fragment2 = Element("div", {"children": ["你好"]})

    # 小于号应该能正确处理
    a = b = 5
    if a <b:
        pass
    elif  a> b:
        pass
    elif a<=b:
        pass
    elif a>=b:
        pass

    list1 = ['color-white', 'color-blue']
    dict1 = {'id': 'aaa'}
    children = [Element("li", {"children": [(i)]}) for i in range(1, 10)]
    return Element("div", {"call-client-script": ["all_FunctionComponent", [("initage", (a))]], "children": [Element("div", {"@click": Element.ClientEmbed(0), "@keydown": Element.ClientEmbed(1), "class": "class1", "keyvalue": f"foo {a} bar", "$$keyvalue": Element.ClientEmbed(2), "hidden": True, "mt-8": True, "id": "special-div", **{ key: True for key in (list1)}, **(dict1), "data-value": (value), "children": ["html中可以嵌入后端渲染的变量内容，以大括号括起来，这部分内容也可以在js中修改，后跟小括号括起来的js内容：", (content1), "这是一个支持", Element("span", {"text-red": True, "children": ["frycss"]}), "语法的div。下面是列表内容：", Element("ul", {"children": [Element("li", {"children": ["0"]}), (Element("li", {"name": (k), "children": [(f"{k}: {v}")]})
             for k, v in props.items() if len(k) > 5), (children), Element("li", {"children": ["99"]})]}), "上述例子演示了html中嵌套python代码，python代码中又嵌套html，html中又 嵌套python代码...其中嵌入的python代码以大括号括起来。 另外还可以看到，嵌入的代码可以是一个generator，嵌入python代码在编译时会自动加上一个小括号， 所以大括号中没必要再加一层小括号或中括号，可以直接写generator，非常方便。 也可以在元素中嵌入前端的响应式内容，以类似markdown加链接的方式括起来：", Element("span", {"*": Element.ClientEmbed(3), "children": [f"初始值: {b}"]}), "&quot;fy中元素内部字符串中的引号是字符串的一部分，所以其中的html元素仍被解析：", Element("div", {"children": ["test"]}), "&quot; 还可以有正常的html：", Element("div", {"class": "normal", "style": ({'display':'block'}), "children": ["这是", Element("span", {"children": ["正常内容"]})]})]})]})

def FunctionComponent2(**props):
    print(f"FunctionComponent2: '{props}'")
    mylist = ('disabled', 'hidden', 'text-cyan-50')
    myprops = {k:v for k,v in props.items() if k != 'children'}
    return Element("div", {"children": [Element(FunctionComponent, {"value": "from FunctionComponent2", "a": '1', "b": (1+2), **(myprops), **{ key: True for key in (mylist)}})]})

def FunctionComponent3(**props):
    print(f"FunctionComponent3: '{props}'")
    return Element("div", {"call-client-script": ["all_FunctionComponent3", []], "children": [Element("div", {"children": [Element("span", {"*": Element.ClientEmbed(0), "children": [f"初始值"]})]})]})

if __name__ == '__main__':
    from fryweb import render
    print("================ FunctionComponent ================")
    print(render(Element(FunctionComponent, {"value": "hello world"})))
    print()
    print("================ FunctionComponent2 ===============")
    print(render(FunctionComponent2))
    print()
    print("================ FunctionComponent2 ===============")
    print(render(FunctionComponent3))
