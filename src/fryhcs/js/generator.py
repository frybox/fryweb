from parsimonious import BadGrammar
from pathlib import Path
import sys
from fryhcs.fry.grammar import grammar
from fryhcs.fry.generator import BaseGenerator
from fryhcs.fileiter import FileIter
from fryhcs.element import ref_attr_name, refall_attr_name
import re
import os
import subprocess
import shutil


# generate js content for fry component
# element$$：代表组件的<script>元素
# hydrate$$：使用embeds$$对html元素树进行水合的函数
# embeds$$： js嵌入值列表
def compose_js(args, script, embeds):
    output = []
    if args:
        args = f'let {{ {", ".join(args)} }} = element$$.fryargs;'

    return f"""\
export {{ hydrate as hydrateAll }} from "fryhcs";
export const hydrate = async function (element$$, doHydrate$$) {{
    {args}
    {script}
    const embeds$$ = [{', '.join(embeds)}];
    doHydrate$$(element$$, embeds$$);
}};
"""


class JSGenerator(BaseGenerator):
    component_pattern = f"**/[A-Z]*-{'[0-9a-fA-Z]'*40}.js"

    def __init__(self, input_files, output_dir):
        super().__init__()
        self.fileiter = FileIter(input_files)
        self.output_dir = Path(output_dir).absolute()
        self.tmp_dir = self.output_dir / '.tmp'

    def generate(self, input_files=[], clean=False):
        if not input_files:
            input_files = self.fileiter.all_files()
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.tmp_dir.mkdir(parents=True, exist_ok=True)
        if clean:
            for f in self.output_dir.glob(self.component_pattern):
                f.unlink(missing_ok=True)
            for f in self.tmp_dir.glob('*.js'):
                f.unlink(missing_ok=True)
        self.dependencies = set()
        count = 0
        for file in input_files:
            self.set_curr_file(file)
            self.js_dir = self.tmp_dir / self.relative_dir
            self.js_dir.mkdir(parents=True, exist_ok=True)
            with self.curr_file.open('r') as f:
                count += self.generate_one(f.read())
        self.bundle()
        return count
                
    def bundle(self):
        if self.dependencies:
            for file, path in self.dependencies:
                p = self.tmp_dir / path
                p.mkdir(parents=True, exist_ok=True)
                shutil.copy(file, p)
        src = list(self.tmp_dir.glob(self.component_pattern))
        if not src:
            return
        this = Path(__file__).absolute().parent
        bun = this / 'bun' 
        env = os.environ.copy()
        if True:
            # 2024.2.23: bun不成熟，使用esbuild打包
            # esbuild支持通过环境变量NODE_PATH设置import查找路径
            env['NODE_PATH'] = str(this / '..' / 'static' / 'js')
            args = ['npx', 'esbuild', '--format=esm', '--bundle', f'--outbase={self.tmp_dir}']
        elif bun.is_file():
            # bun的问题：对于动态import的js，只修改地址，没有打包
            # 暂时不用bun
            args = [str(bun), 'build', '--external', 'fryhcs']
        args += ['--splitting', f'--outdir={self.output_dir}']
        args += [str(js) for js in src]
        subprocess.run(args, env=env)

    def check_js_module(self, jsmodule):
        if jsmodule[0] in "'\"":
            jsmodule = jsmodule[1:-1]
        if jsmodule.startswith('./') or jsmodule.startswith('../'):
            jsfile = self.curr_dir / jsmodule
            jsfile = jsfile.resolve(strict=True) # 如果js文件不存在，抛出异常
            jsdir = jsfile.parent.relative_to(self.curr_root)
            self.dependencies.add((str(jsfile), str(jsdir)))

    def generate_one(self, source):
        tree = grammar.parse(source)
        self.web_components = []
        self.script = ''
        self.args = []
        self.embeds = []
        self.refs = set()
        self.refalls = set()
        self.visit(tree)
        for c in self.web_components:
            name = c['name']
            args = c['args']
            script = c['script']
            embeds = c['embeds']
            jspath = self.js_dir / f'{name}.js'
            with jspath.open('w') as f:
                f.write(compose_js(args, script, embeds))
        return len(self.web_components)

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
                'embeds': self.embeds})
        self.script = ''
        self.args = []
        self.embeds = []
        self.refs = set()
        self.refalls = set()

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

    def visit_js_static_import(self, node, children):
        return children[0]

    def visit_js_simple_static_import(self, node, children):
        _, _, module_name = children
        self.check_js_module(module_name)
        return f'await import({module_name})'

    def visit_js_normal_static_import(self, node, children):
        _import, _, identifiers, _, _from, _, module_name = children
        self.check_js_module(module_name)
        value = ''
        namespace = identifiers.pop('*', '')
        if namespace:
            value = f'const {namespace} = await import({module_name})'
            if identifiers:
                value += ', '
        names = []
        for k,v in identifiers.items():
            if v:
                names.append(f'{k}: {v}')
            else:
                names.append(k)
        if names:
            names = ", ".join(names)
            if namespace:
                value += f'{{{names}}} = {namespace}'
            else:
                value += f'const {{{names}}} = await import({module_name})'
        return value

    def visit_js_import_identifiers(self, node, children):
        identifier, others = children
        identifiers = identifier
        identifiers.update(others)
        return identifiers
        
    def visit_js_other_import_identifiers(self, node, children):
        identifiers = {}
        for ch in children:
            identifiers.update(ch)
        return identifiers

    def visit_js_other_import_identifier(self, node, children):
        _, _comma, _, identifier = children
        return identifier

    def visit_js_import_identifier(self, node, children):
        if isinstance(children[0], str):
            return {'default': children[0]}
        else:
            return children[0]

    def visit_js_identifier(self, node, children):
        return node.text

    def visit_js_namespace_import_identifier(self, node, children):
        _star, _, _as, _, identifier = children
        return {'*': identifier}

    def visit_js_named_import_identifiers(self, node, children):
        _lb, _, identifier, others, _, _rb = children
        identifiers = identifier
        identifiers.update(others)
        return identifiers

    def visit_js_other_named_import_identifiers(self, node, children):
        identifiers = {}
        for ch in children:
            identifiers.update(ch)
        return identifiers

    def visit_js_other_named_import_identifier(self, node, children):
        _, _comma, _, identifier = children
        return identifier

    def visit_js_named_import_identifier(self, node, children):
        value = children[0]
        if isinstance(value, str):
            return {value: ''}
        else:
            return value

    def visit_js_identifier_with_alias(self, node, children):
        identifier, _, _as, _, alias = children
        return {identifier: alias}

    def visit_js_default_export(self, node, children):
        return 'element$$.fryobject ='

    def visit_js_normal_code(self, node, children):
        return node.text

    def visit_no_script_less_than_char(self, node, children):
        return node.text

    def visit_no_comment_slash_char(self, node, children):
        return node.text

    def visit_no_import_i_char(self, node, children):
        return node.text

    def visit_no_export_e_char(self, node, children):
        return node.text
