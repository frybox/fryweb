base_css = {
    ":root, [data-theme=lofi]": {
        "color-scheme":        "light",
        "--primary":           "#0D0D0D",
        "--primary-focus":     "#0D0D0D",
        "--primary-content":   "#ffffff",
        "--secondary":         "#1A1919",
        "--secondary-focus":   "#1A1919",
        "--secondary-content": "#ffffff",
        "--accent":            "#262626",
        "--accent-focus":      "#262626",
        "--accent-content":    "#ffffff",
        "--neutral":           "#000000",
        "--neutral-focus":     "#000000",
        "--neutral-content":   "#ffffff",
        "--base-100":          "#ffffff",
        "--base-200":          "#F2F2F2",
        "--base-300":          "#E6E5E5",
        "--base-content":      "#000000",
        "--info":              "#0070F3",
        "--info-content":      "#ffffff",
        "--success":           "#21CC51",
        "--success-content":   "#000000",
        "--warning":           "#FF6154",
        "--warning-content":   "#ffffff",
        "--error":             "#DE1C8D",
        "--error-content":     "#ffffff",
        "--rounded-box":       "0.25rem",
        "--rounded-btn":       "0.125rem",
        "--rounded-badge":     "0.125rem",
        "--animation-btn":     "0",
        "--animation-input":   "0",
        "--btn-focus-scale":   "1",
        "--tab-radius":        "0",
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

utilities = {
    # 变量定义格式为<name:type>, :type可以省略，省略后默认是'DEFAULT'类型
    'border-<color:semantic-color>': {
        # 在样式值中通过{color}引用变量的值，通过semantic-color['value']计算得出
        'border-color': '{color}',
    },
    'bg-<color:semantic-color>': {
        'background-color': '{color}',
    },
    'text-<color:semantic-color>': {
        'color': '{color}',
    },
    'outline-<color:semantic-color>': {
        'outline-color': '{color}',
    },
    'btn': {
        '@apply': 'gap-2 font-semibold no-underline border-base-200 bg-base-200 text-base-content outline-base-content',
        'active:hover:&, active:focus:&': {
            'animation': 'button-pop 0s ease-out',
            'transform': 'scale(var(--btn-focus-scale, 0.97))',
        },
        'hover-hover:hover:&, active:&': {
            '@apply': 'border-base-300 bg-base-300',
        },
        'focus-visible:&': {
            '@apply': 'outline outline-2 outline-offset-2',
        },
        'border-width': 'var(--border-btn, 1px)',
        'animation': 'button-pop var(--animation-btn, 0.25s) ease-out',
        'text-transform': 'var(--btn-text-case, uppercase)',

# 考虑到性能，不支持在@apply的utility中引用变量（如下面的border-<color>）
# utility中引用变量能极大简化插件编写，但会让pyx转css的过程计算量增加非常多，
# 因为插件加载过程中@apply的utility包含变量时无法转化为样式，只能在某个具体utility转
# css时才能转样式，而这个utility所依赖的utility又会依赖其他utility，这个链条
# 会非常长。
# 不支持引用变量后，插件加载时其中定义的utility直接编译到样式，pyx中的utility转css会加快很多。
#        '@utility:&-<color:brand-color>': {
#            '@apply': 'border-<color> bg-<color> text-<color>-content outline-<color>',
#            'hover-hover:hover:&, active:&': {
#                '@apply': 'border-<color>-focus bg-<color>-focus',
#            },
#        },
#        '@utility: &-<color:state-color>': {
#            '@apply': 'border-<color> bg-<color> text-<color>-content outline-<color>',
#            'hover-hover:hover:&, active:&': {
#                '@apply': 'border-<color> bg-<color>',
#            },
#        },

# 不支持引用变量后，如上两条定义将扩展为如下8条定义：
        '@utility: &-primary': {
            '@apply': 'border-primary bg-primary text-primary-content outline-primary',
            'hover-hover:hover:&': {
                '@apply': 'border-primary-focus bg-primary-focus',
            },
        },
        '@utility: &-secondary': {
            '@apply': 'border-secondary bg-secondary text-secondary-content outline-secondary',
            'hover-hover:hover:&, active:&': {
                '@apply': 'border-secondary-focus bg-secondary-focus',
            },
        },
        '@utility: &-accent': {
            '@apply': 'border-accent bg-accent text-accent-content outline-accent',
            'hover-hover:hover:&, active:&': {
                '@apply': 'border-accent-focus bg-accent-focus',
            },
        },
        '@utility: &-neutral': {
            '@apply': 'border-neutral bg-neutral text-neutral-content outline-neutral',
            'hover-hover:hover:&, active:&': {
                '@apply': 'border-neutral-focus bg-neutral-focus',
            },
        },
        '@utility: &-info': {
            '@apply': 'border-info bg-info text-info-content outline-info',
            'hover-hover:hover:&, active:&': {
                '@apply': 'border-info bg-info',
            },
        },
        '@utility: &-success': {
            '@apply': 'border-success bg-success text-success-content outline-success',
            'hover-hover:hover:&, active:&': {
                '@apply': 'border-success bg-success',
            },
        },
        '@utility: &-warning': {
            '@apply': 'border-warning bg-warning text-warning-content outline-warning',
            'hover-hover:hover:&, active:&': {
                '@apply': 'border-warning bg-warning',
            },
        },
        '@utility: &-error': {
            '@apply': 'border-error bg-error text-error-content outline-error',
            'hover-hover:hover:&, active:&': {
                '@apply': 'border-error bg-error',
            },
        },
    },
}

# generate the following utilities:
# 1. btn
#

types = {
    # default type
    "DEFAULT": {
        "re": ".*",
        "value": lambda v: v,
    },
    # semantic color
    "semantic-color": {
        "re": "primary|primary-focus|primary-content|secondary|secondary-focus-secondary-content|"
              "accent|accent-focus|accent-content|neutral|neutral-focus|neutral-content|"
              "base-100|base-200|base-300|base-content|info|info-content|success|success-content|"
              "warning|warning-content|error|error-content",
        "value": lambda v: f"var(--{v})",
    },
    # brand color
    'brand-color': {
        "re": "primary|secondary|accent|neutral",
        "value": lambda v: f"var(--{v})",
    },
    # state color
    'state-color': {
        "re": "info|success|warning|error",
        "value": lambda v: f"var(--{v})",
    },
}
