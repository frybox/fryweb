print('happybirthday plugin')

base_css = {
    '@keyframes explosion': {
        '0%': {
            'opacity': 0,
        },
        '70%': {
            'opacity': 1,
        },
        '100%': {
            'transform': 'translate(50vw, 100vh)',
        },
    },
    '@keyframes flicker': {
        '0%': {
            'transform': 'skewX(5deg)',
        },
        '25%': {
            'transform': 'skewX(-5deg)',
        },
        '50%': {
            'transform': 'skewX(10deg)',
        },
        '75%': {
            'transform': 'skewX(-10deg)',
        },
        '100%': {
            'transform': 'skewX(5deg)',
        },
    },
}
