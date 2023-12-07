import re

from .modifiers import is_modifier, add_modifier
from .utilities import Utility


def quote_selector(value):
    invalid_chars = r"([~!@$%^&*()+=,./';:\"?><[\]\\{}|`#])"
    fun = lambda m: '\\'+m.group(1)
    return re.sub(invalid_chars, fun, value)


class CSS():
    default_selector_template = '{selector}'
    def __init__(self, key='', value='', toclass=True, generate=True):
        self.key = key
        self.value = value
        self.toclass = toclass
        self.wrappers = []
        self.modifiers = []
        self.utility_args = []
        self.selector = ''
        self.selector_template = self.default_selector_template
        self.styles = []
        self.addons = []
        self.plugin_order = 1000 # 默认最大，优先级最高
        self.level_order = 0
        self.screen_order = []
        self.valid = True
        self.parse()
        if generate:
            self.generate()

    def clone(self):
        css = CSS(generate=False)
        css.key = self.key
        css.value = self.value
        css.toclass = self.toclass
        css.modifiers = self.modifiers[:]
        css.utility_args = self.utility_args[:]
        css.selector = self.selector
        css.selector_template = self.selector_template
        css.styles = self.styles[:]
        css.addons = [addon.clone() for addon in self.addons]
        css.plugin_order = self.plugin_order
        css.level_order = self.level_order
        css.screen_order = self.screen_order
        css.valid = self.valid
        return css

    def update_values(self, args):
        self.styles = [(k, v.format_map(args)) for k,v in self.styles]
        for addon in self.addons:
            addon.update_values(args)

    @property
    def order(self):
        return (self.plugin_order, self.level_order, *self.screen_order)

    @classmethod
    def union(cls, csses):
        # TODO
        pass

    def to_class(self):
        modifiers = ':'.join(self.modifiers)
        utility = '-'.join(self.utility_args)
        if modifiers:
            if utility:
                return modifiers + ':' + utility
            else:
                return modifiers
        else:
            return utility

    def clean_args(self, args):
        # border="~ cyan-100"将被匹配为border和border-cyan-100
        # 而非border-~和border-cyan-100
        if len(args) > 1 and args[-1] == '~':
            return args[:-1]
        return args

    def parse(self):
        """
        for class, key = '';
        for no-value attribute, value = ''
        from:
            self.key
            self.value
        generate:
            self.selector: css selector based on the value of key and value
            self.modifiers: all modifiers
            self.utility_args: utility and its args
        如果utility中的大小为负值，则utility_args[0]以'-'开头
        """
        key = self.key
        value = self.value

        if not key and not value:
            self.modifiers = []
            self.utility_args = []
            self.selector = ''
            return

        if not key:
            # class的css匹配方式: .classname
            selector = '.' + quote_selector(value)
        elif not value:
            # 只有属性名没有值的匹配方式：[key=""]，不能用[key]，
            # [key]匹配的是存在属性key，此时key的值可以是任意值；
            # 也不能用[key ~= ""]，这个无法匹配只有属性名的情况。
            selector = '[' + quote_selector(key) + ' = ""]'
        else:
            # 既有属性又有值的情况，与类的情况类似，值中使用空格分开
            # 的每一个"子值"，都是用[key ~= subvalue]进行匹配
            selector = '[' + quote_selector(key) + ' ~= "' + value + '"]'

        keys = key.split(':') if key else []
        values = value.split(':') if value else []
        negative = False
        if keys and not is_modifier(keys[-1]):
            modifiers = keys[:-1]
            utility = keys[-1]
            if utility and utility[0] == '-':
                utility = utility[1:]
                negative = not negative
            if utility:
                utility_args = utility.split('-')
            else:
                utility_args = []
        else:
            modifiers = keys[:]
            utility_args = []
        if values:
            modifiers += values[:-1]
            utility = values[-1]
            if utility and utility[0] == '-':
                utility = utility[1:]
                negative = not negative
            if utility:
                utility_args += utility.split('-')
        if negative and utility_args:
            utility_args[0] = '-' + utility_args[0]

        self.modifiers = modifiers
        self.utility_args = self.clean_args(utility_args)
        self.selector = selector
        if self.toclass:
            self.selector = '.' + quote_selector(self.to_class())

    def generate(self):
        """
        from:
            self.modifiers
            self.utility_args
        generate:
            self.wrappers
            self.selector_template
            self.styles
            self.addons
        """
        for modifier in self.modifiers:
            if not add_modifier(self, modifier):
                self.valid = False
                return
        self.utility = Utility(self)
        self.valid = self.utility()
    
    def add_style(self, key, value):
        style = (key, value)
        self.styles.append(style)

    def get_style(self, key):
        for k, v in self.styles:
            if k == key:
                return v
        return None

    def new_addon(self, key='', value='', generate=False):
        addon = CSS(key, value, generate)
        self.addons.append(addon)
        return addon

    def add_addon(self, addon):
        self.addons.append(addon)

    def quote(self, value):
        return quote_selector(value)

    def has_styles(self):
        if not self.valid:
            return False
        if len(self.styles) > 0:
            return True
        return any(addon.has_styles() for addon in self.addons)

    def lines(self, new_selector=''):
        if not self.valid:
            return []
        twospace = '  '
        indent = ''
        lines = []
        if not self.has_styles():
            return lines
        for wrapper in self.wrappers:
            lines.append(indent + wrapper + ' {')
            indent += twospace
        selector = new_selector or self.selector
        selector = self.selector_template.format(selector=selector)
        if len(self.styles) > 0:
            lines.append(indent + selector + ' {')
            indent += twospace
            for k, v in dict(self.styles).items():
                style = f'{k}: {v};'
                lines.append(indent + style)
            indent = indent[:-2]
            lines.append(indent + '}')
        for addon in self.addons:
            lines.append('')
            for line in addon.lines(selector):
                lines.append(indent + line)
        while len(indent) > 0:
            indent = indent[:-2]
            lines.append(indent + '}')
        return lines

    def text(self):
        return '\n'.join(self.lines()) + '\n\n'
