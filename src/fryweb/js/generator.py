from parsimonious import BadGrammar
from pathlib import Path
import time
from fryweb.fry.grammar import grammar
from fryweb.fry.generator import BaseGenerator
from fryweb.fileiter import FileIter
from fryweb.element import ref_attr_name, refall_attr_name
import re
import os
import subprocess
import shutil
import tempfile


# generate js content for fry component
# this：代表组件对象
# embeds： js嵌入值列表
# emports: 静态import语句
def compose_js(args, script, embeds, imports):
    if imports:
        imports = '\n'.join(imports)
    else:
        imports = ''

    if args:
        args = f'let {{ {", ".join(args)} }} = this.fryargs;'
    else:
        args = ''

    return f"""\
{imports}
export const setup = async function () {{
    {args}
    {script}
    this.fryembeds = [{', '.join(embeds)}];
}};
"""

def compose_index(src, root_dir):
    dest = root_dir / 'index.js'
    output = []
    names = []
    for file in src:
        f = file.relative_to(root_dir)
        suffix_len = len(f.suffix)
        path = f.as_posix()[:-suffix_len]
        name = f.stem
        output.append(f'import {{ setup as {name} }} from "./{path}";')
        names.append(name)
    output.append(f'let setups = {{ {", ".join(names)} }};')
    output.append('import { hydrate as hydrate_with_setups } from "fryweb";')
    output.append('export const hydrate = async (rootElement) => await hydrate_with_setups(rootElement, setups);')
    output = '\n'.join(output)
    with dest.open('w', encoding='utf-8') as f:
        f.write(output)
    return dest


def is_componentjs(file):
    if re.match(r'^![A-Z][a-zA-Z0-9_]*@[a-zA-Z_][a-zA-Z0-9_]+\.js$', file.name):
        return True
    return False

def get_componentjs(rootdir):
    for file in rootdir.rglob("*.js"):
        if is_componentjs(file):
            yield file

class JsGenerator(BaseGenerator):
    def __init__(self):
        super().__init__()
        self.dependencies = set()

    def generate(self, tree, hash, curr_root, curr_file):
        self.curr_root = curr_root
        self.curr_dir = curr_file.parent
        self.relative_dir = self.curr_dir.relative_to(curr_root)
        self.js_dir = fryconfig.build_root / self.relative_dir
        self.js_dir.mkdir(parents=True, exist_ok=True)
        for file in self.js_dir.glob(f'!*@{curr_file.stem}.js'):
            file.unlink(missing_ok=True)
        self.web_components = []
        self.script = ''
        self.args = []
        self.embeds = []
        self.refs = set()
        self.refalls = set()
        self.static_imports = []
        self.visit(tree)

        for c in self.web_components:
            name = c['name']
            args = c['args']
            script = c['script']
            embeds = c['embeds']
            imports = c['imports']
            jspath = self.js_dir / f'!{name}@{curr_file.stem}.js'
            with jspath.open('w', encoding='utf-8') as f:
                f.write(f'// fry {hash}\n')
                f.write(compose_js(args, script, embeds, imports))
        return len(self.web_components)

    def bundle(self):
        if self.dependencies:
            deps = set()
            for dir, root in self.dependencies:
                for f in dir.rglob('*.[jt]s'):
                    if f.is_relative_to(fryconfig.build_root):
                        continue
                    if is_componentjs(f):
                        continue
                    p = f.parent.relative_to(root)
                    deps.add((f, p))
            for file, path in deps:
                p = fryconfig.build_root / path
                p.mkdir(parents=True, exist_ok=True)
                shutil.copy(file, p)
        src = list(get_componentjs(fryconfig.build_root))
        if not src:
            return
        entry_point = compose_index(src, fryconfig.build_root) 
        outfile = fryconfig.js_file
        this = Path(__file__).absolute().parent
        bun = this / 'bun' 
        env = os.environ.copy()
        if True:
            # 2024.2.23: bun不成熟，使用esbuild打包
            # esbuild支持通过环境变量NODE_PATH设置import查找路径
            env['NODE_PATH'] = str(this / '..' / 'static' / 'js')
            # Windows上需要指定npx全路径，否则会出现FileNotFoundError
            npx = shutil.which('npx')
            if not npx:
                print(f"Can't find npx, please install nodejs first.")
                return
            args = [npx, 'esbuild', '--format=esm', '--bundle', '--minify', '--sourcemap', f'--outfile={outfile}', str(entry_point),]
        elif bun.is_file():
            # bun的问题：对于动态import的js，只修改地址，没有打包
            # 暂时不用bun
            args = [str(bun), 'build', '--external', 'fryweb', '--splitting', f'--outdir={outfile.parent}', str(entry_point)]
        subprocess.run(args, env=env)

    def check_js_module(self, jsmodule):
        if jsmodule[0] in "'\"":
            jsmodule = jsmodule[1:-1]
        if jsmodule.startswith('./'):
            self.dependencies.add((self.curr_dir, self.curr_root))
        elif jsmodule.startswith('../'):
            self.dependencies.add((self.curr_dir.parent.absolute(), self.curr_root))

    def generic_visit(self, node, children):
        return children or node

    def visit_single_quote(self, node, children):
        return node.text

    def visit_double_quote(self, node, children):
        return node.text

    def visit_py_simple_quote(self, node, children):
        return children[0]

    def visit_js_simple_quote(self, node, children):
        return children[0]

    def visit_fry_component(self, node, children):
        cname, _fryscript, _template, _script = children
        if self.script or self.embeds or self.refs or self.refalls:
            uuid = self.get_uuid(cname, node)
            self.web_components.append({
                'name': uuid,
                'args': [*self.refs, *self.refalls, *self.args],
                'script': self.script,
                'embeds': self.embeds,
                'imports': self.static_imports})
        self.script = ''
        self.args = []
        self.embeds = []
        self.refs = set()
        self.refalls = set()
        self.static_imports = []

    def visit_fry_component_header(self, node, children):
        _def, _, cname, _ = children
        return cname

    def visit_fry_component_name(self, node, children):
        return node.text

    def visit_fry_attributes(self, node, children):
        return [ch for ch in children if ch]

    def visit_fry_spaced_attribute(self, node, children):
        _, attr = children
        return attr

    def visit_fry_attribute(self, node, children):
        return children[0]

    def visit_same_name_attribute(self, node, children):
        _l, _, identifier, _, _r = children
        return identifier

    def visit_py_identifier(self, node, children):
        return node.text

    def visit_fry_embed_spread_attribute(self, node, children):
        return None

    def visit_fry_kv_attribute(self, node, children):
        name, _, _, _, value = children
        name = name.strip()
        if name == ref_attr_name:
            _type, script = value
            value = script.strip()
            if value in self.refs or value in self.refalls:
                raise BadGrammar(f"Duplicated ref name '{value}', please use 'refall'")
            self.refs.add(value)
            return None
        elif name == refall_attr_name:
            _type, script = value
            value = script.strip()
            if value in self.refs:
                raise BadGrammar(f"Ref name '{value}' exists, please use another name for 'refall'")
            self.refalls.add(value)
            return None
        elif isinstance(value, tuple) and value[0] == 'js_embed':
            script = value[1]
            self.embeds.append(script)
        return name

    def visit_fry_novalue_attribute(self, node, children):
        return children[0]

    def visit_fry_attribute_name(self, node, children):
        return node.text

    def visit_fry_attribute_value(self, node, children):
        return children[0]

    def visit_joint_html_embed(self, node, children):
        _, _f_string, _, jsembed = children
        _name, script = jsembed
        self.embeds.append(script)
        return None

    def visit_joint_embed(self, node, children):
        _f_string, _, jsembed = children
        _name, script = jsembed
        self.embeds.append(script)
        return None

    def visit_web_script(self, node, children):
        _, _begin, attributes, _, _greaterthan, script, _end = children
        self.args = [k for k in attributes if k]
        self.script = script

    def visit_js_script(self, node, children):
        return ''.join(str(ch) for ch in children)

    def visit_js_embed(self, node, children):
        _, script, _ = children
        return ('js_embed', script)

    def visit_js_parenthesis(self, node, children):
        _, script, _ = children
        return '(' + script + ')'

    def visit_js_brace(self, node, children):
        _, script, _ = children
        return '{' + script + '}'

    def visit_js_script_item(self, node, children):
        return children[0]

    def visit_js_single_line_comment(self, node, children):
        return node.text

    def visit_js_multi_line_comment(self, node, children):
        return node.text

    def visit_js_regexp(self, node, children):
        return node.text

    def visit_js_template_simple(self, node, children):
        return node.text

    def visit_js_template_normal(self, node, children):
        return node.text

    # 2024.11.28: 修改import的实现，静态import仍然是静态，挪到setup函数之外，import内容变为闭包变量使用
    def visit_js_static_import(self, node, children):
        self.static_imports.append(children[0])
        return ''

    def visit_js_simple_static_import(self, node, children):
        _, _, module_name, _, _ = children
        self.check_js_module(module_name)
        return node.text

    def visit_js_normal_static_import(self, node, children):
        _import, _, identifiers, _, _from, _, module_name, _, _ = children
        self.check_js_module(module_name)
        return node.text

    # 2024.11.9: 去掉对export default的支持，直接使用this.prop1 = prop1
    #def visit_js_default_export(self, node, children):
    #    return '$fryobject ='

    def visit_js_normal_code(self, node, children):
        return node.text

    def visit_no_script_less_than_char(self, node, children):
        return node.text

    def visit_no_comment_slash_char(self, node, children):
        return node.text

    def visit_no_import_i_char(self, node, children):
        return node.text

    # 2024.11.9: 去掉对export default的支持，直接使用this.prop1 = prop1
    #def visit_no_export_e_char(self, node, children):
    #    return node.text
