from fryhcs import Element
from random import randint

style = f'text-cyan-{randint(1, 9)*100} bg-#6667'
#a = <span $style={style}>[](3)</span>
a = <span $class="bg-cyan-200 absolute" $style={style}>[初{1}始{2}值](3)</span>
#a = <span $style={style}>[初始值](1)</span>

if __name__ == '__main__':
    from fryhcs import render
    print(render(a))
