from parsimonious import VisitationError
from pathlib import Path
import sys
from fryhcs.fry.grammar import grammar
from fryhcs.fry.generator import BaseGenerator
from fryhcs.fileiter import FileIter
import re
import os
import subprocess


# generate js content for fry component
def compose_js(args, script, embeds):
    output = []
    if args:
        args = ', '.join(args)
        args = f'const {args} = script$$.fryargs;'

    embeds = ', '.join(embeds)

    # 为了拿到当前的这个组件元素(document.currentScript)，以及为了每个script标签都执行一次，
    # 不得不将module类型的script转化为标准html script。
    return f"""\
import {{hydrate as hydrate$$}} from "fryhcs";
export const hydrate = async function (script$$) {{
    {args}
    {script}
    const rootElement$$ = script$$.parentElement;
    const componentId$$ = script$$.dataset.fryid;
    const embeds$$ = [{embeds}];
    hydrate$$(rootElement$$, componentId$$, embeds$$);
}};
"""


class JSGenerator(BaseGenerator):
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
            pattern = '[0-9a-f]'*40+'.js'
            for f in self.output_dir.glob(pattern):
                f.unlink(missing_ok=True)
            for f in self.tmp_dir.glob('*.js'):
                f.unlink(missing_ok=True)
        count = 0
        for file in input_files:
            with file.open('r') as f:
                count += self.generate_one(f.read())
        self.bundle()
        return count
                
    def bundle(self):
        src = list(self.tmp_dir.glob('*.js'))
        if not src:
            return
        this = Path(__file__).absolute().parent
        bun = this / 'bun' 
        env = os.environ.copy()
        if True:
            env['NODE_PATH'] = str(this / '..' / 'static' / 'js')
            args = ['npx', 'esbuild', '--format=esm', '--bundle']
        elif bun.is_file():
            # 对于动态import的js，只修改地址，没有打包
            # 暂时不用bun
            args = [str(bun), 'build', '--external', 'fryhcs']
        args += ['--splitting', f'--outdir={self.output_dir}']
        args += [str(js) for js in src]
        subprocess.run(args, env=env)

    def generate_one(self, source):
        tree = grammar.parse(source)
        self.web_components = []
        self.script = ''
        self.args = []
        self.embeds = []
        self.visit(tree)
        for c in self.web_components:
            name = c['name']
            args = c['args']
            script = c['script']
            embeds = c['embeds']
            jspath = self.tmp_dir / f'{name}.js'
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

    def visit_fry_simple_quote(self, node, children):
        return children[0]

    def visit_js_simple_quote(self, node, children):
        return children[0]

    def visit_fry_element_with_web_script(self, node, children):
        if self.script or self.embeds:
            uuid = self.get_uuid(node)
            self.web_components.append({
                'name': uuid,
                'args': self.args,
                'script': self.script,
                'embeds': self.embeds})
        self.script = ''
        self.args = []
        self.embeds = []

    def visit_fry_attributes(self, node, children):
        return [ch for ch in children if ch]

    def visit_fry_spaced_attribute(self, node, children):
        _, attr = children
        return attr

    def visit_fry_attribute(self, node, children):
        return children[0]

    def visit_fry_embed_spread_attribute(self, node, children):
        return None

    def visit_fry_kv_attribute(self, node, children):
        name, _, _, _, _value = children
        return name

    def visit_fry_novalue_attribute(self, node, children):
        return children[0]

    def visit_fry_attribute_name(self, node, children):
        return node.text

    def visit_fry_attribute_value(self, node, children):
        return children[0]

    def visit_web_script(self, node, children):
        _, _sep, _, _begin, attributes, _, _lessthan, script, _end = children
        self.args = [k for k in attributes if k]
        self.script = script

    def visit_js_script(self, node, children):
        return ''.join(str(ch) for ch in children)

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

    def visit_local_js_embed(self, node, children):
        _, script, _ = children
        self.embeds.append(script)
        return script

    def visit_js_parenthesis(self, node, children):
        _, script, _ = children
        return '(' + script + ')'

    def visit_js_brace(self, node, children):
        _, script, _ = children
        return '{' + script + '}'

    def visit_js_static_import(self, node, children):
        return children[0]

    def visit_js_simple_static_import(self, node, children):
        _, _, module_name = children
        return f'await import({module_name})'

    def visit_js_normal_static_import(self, node, children):
        _import, _, identifiers, _, _from, _, module_name = children
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
        return 'script$$.fryobject ='

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
