from fryhcs import Element
from random import randint

style = f'text-cyan-{randint(1, 9)*100} bg-#6667'
a = <span $style={style}>{1}</span>

if __name__ == '__main__':
    from fryhcs import render
    print(render(a))
