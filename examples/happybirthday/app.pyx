from fryhcs import Element, html
from fryhcs.css import random_color
from random import randint
from flask import Flask

app = Flask(__name__)
app.config['FRYHCS_PLUGINS'] = ['happybirthday']

@app.get('/')
def index():
    return html(HappyBirthday, title="生日快乐~")

def Bokeh(props):
    bg = random_color((200,250), (50,150), (50,150))
    x = randint(1, 99)
    y = randint(10, 90)
    duration = randint(100, 400)/100
    delay = randint(10, 400)/100
    return (
      <div fixed w-2vmin h-2vmin rounded-50%
           animate="name-explosion reverse infinite ease-0.84-0.02-1-1"
           $style={(f"bg-{bg} translate-x-{x}vw translate-y-{y}vh",
                    f"animate-duration-{duration}s -animate-delay-{delay}s")}>
      </div>
    )

def Candle(props):
    return <div>
           </div>

def Cake(props):
    return <div>
           </div>

def Plate(props):
    return <div h-90px w-300px rounded-full
                bg-radial from-08c7fe via-04d7f2 via-71 to-02ffd0 to-100
                absolute bottom-2
                shadow-nm shadow-00e2e1>
           </div>

def SettledCake(props):
    return <div w-30%>
             <div z-10> <Candle/> </div>
             <div z-5>  <Cake/>   </div>
             <div z-1>  <Plate/>  </div>
           </div>

def HappyBirthday(props):
    return (
      <div flex bg-gradient-to-r from-fuchsia-200 to-indigo-200 w-full h-100vh>
        {<Bokeh/> for i in range(20)}

        <div flex justify-center w-full>
          <SettledCake />
        </div>
      </div>
    )

if __name__ == '__main__':
    from fryhcs import render
    print("render HappyBirthday")
    print(render(HappyBirthday))
    print()
    print("render html")
    print(html(HappyBirthday, title="生日快乐"))
