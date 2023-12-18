print("daisyui plugin")

def base_css():
    return {
        ":root, [data-theme=lofi]": {
            "color-scheme":        "light",
            "--rounded-box":       "0.25rem",
            "--rounded-btn":       "0.125rem",
            "--rounded-badge":     "0.125rem",
            "--animation-btn":     "0",
            "--animation-input":   "0",
            "--btn-focus-scale":   "1",
            "--tab-radius":        "0",
            "--cool":              "65 65 65",
            "--coll-content":      "250 250 250",
            "--coll-focus":        "30 30 30",
            "--base-200":          "40 40 40",
            "--base-300":          "30 30 30",
            "--base-content":      "100 100 100",
        },
        "@keyframes button-pop": {
          "0%": {
            "transform": "scale(var(--btn-focus-scale, 0.98))",
          },
          "40%": {
            "transform": "scale(1.02)",
          },
          "100%": {
            "transform": "scale(1)",
          },
        },
    }

def utilities():
    return [
        # 2023.12.16 暂不支持动态utility，不支持utility名中包含变量，semantic_color已经可以解决绝大部分变量的需求了
        ## 变量定义格式为<name:type>, :type可以省略，省略后默认是'DEFAULT'类型
        #('border-<color:state-color>', 
        #    # 在样式值中通过{color}引用变量的值，通过semantic-color['value']计算得出
        #    ('border-color', '{color}')),
        ('btn',
          ('@apply', 'gap-2 font-semibold no-underline border-base-200',
            'bg-base-200 text-base-content outline-base-content'),
          ('active:hover:&, active:focus:&', 
            ('animation', 'button-pop 0s ease-out'),
            ('transform', 'scale(var(--btn-focus-scale, 0.97))')),
          ('hover-hover:hover:&, active:&', ('@apply', 'border-base-300 bg-base-300')),
          ('focus-visible:&', ('@apply', 'outline outline-2 outline-offset-2')),
          ('border-width', 'var(--border-btn, 1px)'),
          ('animation', 'button-pop var(--animation-btn, 0.25s) ease-out'),
          ('text-transform', 'var(--btn-text-case, uppercase)')),

        # 考虑到性能，不支持在@apply的utility中引用变量（如下面的border-<color>）
        # utility中引用变量能极大简化插件编写，但会让fry转css的过程计算量增加非常多，
        # 因为插件加载过程中@apply的utility包含变量时无法转化为样式，只能在某个具体utility转
        # css时才能转样式，而这个utility所依赖的utility又会依赖其他utility，这个链条
        # 会非常长。
        # 不支持引用变量后，插件加载时其中定义的utility直接编译到样式，fry中的utility转css会加快很多。
        #    ('btn-<color:state-color>', 
        #      ('@apply', 'border-<color> bg-<color> text-<color>-content outline-<color>'),
        #      ('hover-hover:hover:&', 
        #        ('@apply', 'border-<color>-focus bg-<color>-focus'))),

        ('btn-cool',
          ('@apply', 'border-cool bg-cool text-cool-content outline-cool'),
          ('hover-hover:hover:&',
            ('@apply', 'border-cool-focus bg-cool-focus'))),
    ]

def colors():
    return {
        'cool': 'rgb(var(--cool))',
        'cool-content': 'rgb(var(--cool-content))',
        'cool-focus': 'rgb(var(--cool-focus))',
        'base-200': 'rgb(var(--base-200))',
        'base-300': 'rgb(var(--base-300))',
        'base-content': 'rgb(var(--base-content))',
    }
