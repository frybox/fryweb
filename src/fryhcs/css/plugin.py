from fryhcs.config import fryconfig
from fryhcs.css.style import CSS
from importlib import import_module
import re

class PluginError(Exception):
    pass

base_csses = []
static_utilities = {}
dynamic_utilities = {}

def load_plugins():
    for pid, plugin in enumerate(fryconfig.plugins):
        module = import_module(plugin)
        if module:
            load_plugin(pid, module)

def load_plugin(pid, plugin):
    base_css = getattr(plugin, 'base_css', {})
    utilities = getattr(plugin, 'utilities', {})
    types = getattr(plugin, 'types', {})

    if base_css:
        base_csses.append(base_css)

    level = 0

    for name, content in utilities.items():
        load_utility(name, content, types, pid, level)

# utility1: "btn-<color:state-color>-focus"
# return1:  "btn-(info|success|warning|error)-focus", [("color", lambda v: f"var(--{v})")]
# utility2: "btn"
# return2:  "btn", []
def parse_name(utility, types):
    r = '<([0-9a-zA-Z_-]+)(?::([0-9a-zA-Z_-]+))?>'
    vs = []
    lb = 0
    names = [] 
    for m in re.finditer(r, utility):
        begin, end = m.span()
        name, t = m.groups()
        if t is None:
            t = 'DEFAULT'
        tt = types[t]
        names.append(utility[lb:begin])
        names.append('(')
        names.append(tt['re'])
        names.append(')')
        vs.append((name, tt['value']))
        lb = end
    names.append(utility[lb:])
    return (''.join(names), vs)

def prepare_content(content):
    newcontent = {}
    def add(n, v):
        n = n.strip()
        if not n in newcontent:
            newcontent[n] = v
        elif isinstance(v, dict) and isinstance(newcontent[n], dict):
            newcontent[n].update(v)
        else:
            raise PluginError(f"Duplicate name '{n}'")
    for name, value in content.items():
        if ',' in name:
            for n in name.split(','):
                add(n, value)
        else:
            add(name, value)
    return newcontent


def load_subutilities(prefix, content):
    defaultcss = CSS(key=prefix, value='dummy')
    subcsses = []
    for key, value in content.items():
        if key == '@apply':
            if not isinstance(value, str):
                raise PluginError(f"@apply can only have string value, not '{value}'.")
            subutils = value.split()
            subcsses += [CSS(key=prefix, value=v) for v in subutils]
        elif '&' in key:
            raise PluginError(f"Subutilities can't have this kind of key: '{key}'")
        elif isinstance(value, str):
            defaultcss.add_style(key, value)
        else:
            raise PluginError(f"Invalid '{name}': '{value}'")
    subcsses.insert(0, defaultcss)
    return subcsses

def load_utility(name, content, types, pid, level):
    regexp, variables = parse_name(name, types)
    content = prepare_content(content)
    defaultcss = CSS()
    defaultcss.selector = regexp
    defaultcss._variables = variables
    defaultcss.plugin_order = pid
    defaultcss.level_order = level
    subcsses = []
    for key, value in content.items():
        if key == '@apply':
            if not isinstance(value, str):
                raise PluginError(f"@apply can only have string value, not '{value}'.")
            subutils = value.split()
            subcsses += [CSS(value=v) for v in subutils]
        elif key.startswith('@utility:'):
            if not isinstance(value, dict):
                raise PluginError(f"New sub-utility '{key}' should have dict value.")
            key = key.split(':',1)[1].strip()
            key = key.replace('&', name)
            load_utility(key, value, types, pid, level+1)
        elif key.endswith(':&'):
            if '&' in key[:-2]:
                raise PluginError(f"Invalid format for '{key}'.")
            subcsses += load_subutilities(key[:-2], value)
        elif isinstance(value, str):
            defaultcss.add_style(key, value)
        else:
            raise PluginError(f"Invalid '{name}': '{value}'")
    csses = {}
    for css in subcsses:
        key = (css.selector_template, *css.wrappers)
        if key in csses:
            csses[key].styles += css.styles
        else:
            csses[key] = css
    defaultkey = (defaultcss.selector_template, *defaultcss.wrappers)
    if defaultkey in csses:
        css = csses.pop(defaultkey)
        defaultcss.styles += css.styles
    for css in sorted(csses.values(), key=lambda c: c.order):
        defaultcss.add_addon(css)
    if defaultcss._variables:
        dynamic_utilities[defaultcss.selector] = defaultcss
    else:
        static_utilities[defaultcss.selector] = defaultcss

def plugin_utility(utility_args):
    utility = '-'.join(utility_args)
    if utility in static_utilities:
        clone = static_utilities[utility].clone()
        return clone
    for regexp in dynamic_utilities.keys():
        # 动态utility可能有负号，负号被放到utility之前，处理负号的情况
        negative = ''
        if utility[0] == '-':
            negative = '-'
            utility = utility[1:]
        match = re.fullmatch(regexp, utility)
        if match:
            du = dynamic_utilities[regexp]
            values = match.groups()
            args = {'NEGATIVE': negative}
            for val, var in zip(values, du._variables):
                args[var[0]] = var[1](val)
            clone = du.clone()
            clone.update_values(args)
            return clone
    return None 

def plugin_basecss():
    output = []
    def lines(base, indent):
        for key, value in base.items():
            if isinstance(value, (str, int)):
                output.append(f'{indent}{key}: {value};')
            elif isinstance(value, (list, tuple)):
                output.append(f'{indent}{key}: {" ".join(str(x) for x in value)};')
            elif isinstance(value, dict):
                output.append(f'{indent}{key} {{')
                lines(value, indent+'  ')
                output.append(f'{indent}}}')

    for basecss in base_csses:
        lines(basecss, '')
    return '\n'.join(output)+'\n'

load_plugins()
