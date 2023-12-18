from fryhcs.config import fryconfig
from fryhcs.css.style import CSS
from importlib import import_module
import re

class PluginError(Exception):
    pass

base_csses = []
static_utilities = {}
dynamic_utilities = {}
semantic_colors = {}

def load_plugins():
    for pid, plugin in enumerate(fryconfig.plugins):
        module = import_module(plugin)
        if module:
            load_plugin(pid, module)

def load_plugin(pid, plugin):
    base_css = getattr(plugin, 'base_css', lambda:{})()
    utilities = getattr(plugin, 'utilities', lambda:{})()
    #types = getattr(plugin, 'types', lambda:{})()
    colors = getattr(plugin, 'colors', lambda:{})()

    if base_css:
        base_csses.append(base_css)

    if colors:
        semantic_colors.update(colors)

    level = 0
    for name, content in prepare_utilities(utilities):
        #load_utility(name, content, types, pid, level)
        load_utility(name, content, pid, level)
        level += 1


def prepare_utilities(utilities):
    newlist = []
    newdict = {}
    def add(n, v):
        n = n.strip()
        if ':' in n:
            raise RuntimeError(f"Custom utility should not has modifiers: '{n}'")
        if not n in newdict:
            newdict[n] = v
            newlist.append((n,v))
        else:
            newdict[n] += v
    for name, *value in utilities:
        if ',' in name:
            for n in name.split(','):
                add(n, value[:])
        else:
            add(name, value)
    return newlist


# 2023.12.16 新定义的utility名中暂不支持变量，有了colors后，变量意义已经不大了。
## utility1: "btn-<color:state-color>-focus"
## return1:  "btn-(info|success|warning|error)-focus", [("color", lambda v: f"var(--{v})")]
## utility2: "btn"
## return2:  "btn", []
#def parse_name(utility, types):
#    r = '<([0-9a-zA-Z_-]+)(?::([0-9a-zA-Z_-]+))?>'
#    vs = []
#    lb = 0
#    names = [] 
#    for m in re.finditer(r, utility):
#        begin, end = m.span()
#        name, t = m.groups()
#        if t is None:
#            t = 'DEFAULT'
#        tt = types[t]
#        names.append(utility[lb:begin])
#        names.append('(')
#        names.append(tt['re'])
#        names.append(')')
#        vs.append((name, tt['value']))
#        lb = end
#    names.append(utility[lb:])
#    return (''.join(names), vs)


def prepare_content(content):
    newlist = []
    for name, *value in content:
        if ',' in name:
            for n in name.split(','):
                newlist.append((n.strip(), value))
        else:
            newlist.append((name.strip(), value))
    return newlist


def load_subutilities(prefix, content):
    dummy = None
    subcsses = []
    for key, *value in content:
        if key == '@apply':
            dummy = None
            if not all(isinstance(v, str) for v in value):
                raise PluginError(f"@apply can only have string values, not '{value}'.")
            value = ' '.join(value)
            subutils = value.split()
            subcsses += [CSS(key=prefix, value=v) for v in subutils]
        elif '&' in key or ',' in key:
            raise PluginError(f"Subutilities can't have this kind of key: '{key}'")
        elif len(value) == 1 and isinstance(value[0], str):
            if not dummy:
                dummy = CSS(key=prefix, value='dummy')
                subcsses.append(dummy)
            dummy.add_style(key, value[0])
        else:
            raise PluginError(f"Invalid '{name}': '{value}'")
    return subcsses

#def load_utility(name, content, types, pid, level):
def load_utility(name, content, pid, level):
    #regexp, variables = parse_name(name, types)
    content = prepare_content(content)
    dummy = None
    defaultcss = CSS()
    #defaultcss.selector = regexp
    #defaultcss._variables = variables
    defaultcss.selector = name
    defaultcss.plugin_order = pid
    defaultcss.level_order = level
    subcsses = []
    for key, value in content:
        if key == '@apply':
            dummy = None
            if not all(isinstance(v, str) for v in value):
                raise PluginError(f"@apply can only have string values, not '{value}'.")
            value = ' '.join(value)
            subutils = value.split()
            subcsses += [CSS(value=v) for v in subutils]
        elif key.endswith(':&'):
            dummy = None
            if '&' in key[:-2]:
                raise PluginError(f"Invalid format for '{key}'.")
            subcsses += load_subutilities(key[:-2], value)
        elif len(value) == 1 and isinstance(value[0], str):
            if not dummy:
                dummy = CSS()
                subcsses.append(dummy)
            dummy.add_style(key, value[0])
        else:
            raise PluginError(f"Invalid '{name}': '{value}'")
    csses = defaultcss.addons
    lastkey = None
    for css in subcsses:
        key = (css.selector_template, *css.wrappers)
        if key == lastkey:
            csses[-1].styles += css.styles
        else:
            csses.append(css)
            lastkey = key
    static_utilities[defaultcss.selector] = defaultcss


def plugin_utility(utility_args):
    utility = '-'.join(utility_args)
    if utility in static_utilities:
        clone = static_utilities[utility].clone()
        return clone
    # 2023.12.16 暂不支持动态utility，有了colors后动态utility意义已经不大了
    #for regexp in dynamic_utilities.keys():
    #    # 动态utility可能有负号，负号被放到utility之前，处理负号的情况
    #    negative = ''
    #    if utility[0] == '-':
    #        negative = '-'
    #        utility = utility[1:]
    #    match = re.fullmatch(regexp, utility)
    #    if match:
    #        du = dynamic_utilities[regexp]
    #        values = match.groups()
    #        args = {'NEGATIVE': negative}
    #        for val, var in zip(values, du._variables):
    #            args[var[0]] = var[1](val)
    #        clone = du.clone()
    #        clone.update_values(args)
    #        return clone
    return None 

def plugin_color(arg):
    return semantic_colors.get(arg, None)

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
