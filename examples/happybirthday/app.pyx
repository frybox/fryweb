from fryhcs import Element, html
from fryhcs.css import random_color
from random import randint
from flask import Flask

app = Flask(__name__)
app.config['FRYHCS_PLUGINS'] = ['happybirthday']

@app.get('/')
def index():
    return html(HappyBirthday, title="生日快乐~")

def Bokeh(**props):
    bg = random_color((200,250), (50,150), (50,150))
    x = randint(1, 99)
    y = randint(10, 90)
    duration = randint(100, 400)/100
    delay = randint(10, 400)/100
    return (
      <div fixed w-2vmin h-2vmin rounded-50%
           animate="name-explosion reverse infinite ease-0.84-0.02-1-1"
           $style={f"bg-{bg} translate-x-{x}vw translate-y-{y}vh",
                   f"animate-duration-{duration}s -animate-delay-{delay}s"}>
      </div>
    )

def Candle(**props):
    return (
         <div absolute bottom-150px h-50px w-12px
              bg-gradient-to-t from-b7f4a7 to-white>
           <div bg-gradient-to-b from-fff6d9 to-fbc36c
                w-15px h-35px
                rounded-t-10px_35px rounded-b-10px
                shadow-0_0_17px_7px_rgba(251,246,190,0.71)
                relative -top-35px
                origin-bottom
                animate="name-flicker duration-1s ease-in-out alternate infinite">
           </div>
         </div>)

def Cake(**props):
    def yc():
        for i in range(4, 84, 4):
            yield i, random_color((100, 255), (200, 255))

    styles = {
        'box-shadow': ', '.join(f"0px {y}px 0px {c}" for y, c in yc())
    }
    return <div w-200px h-60px rounded-100% bg-f9fdff
                absolute bottom-110px
                style={styles}>
           </div>

def Plate(**props):
    return <div h-90px w-300px rounded-100%
                bg-radial from-#08c7fe via-#04d7f2 via-71 to-#02ffd0 to-100
                absolute bottom-10px
                shadow-nm shadow-00e2e1>
           </div>

def SettledCake(**props):
    return <div absolute bottom-0 flex justify-center w-60%>
             <div relative flex justify-center z-10> <Candle/> </div>
             <div relative flex justify-center z-5>  <Cake/>   </div>
             <div relative flex justify-center z-1>  <Plate/>  </div>
           </div>

def HappyBirthday(**props):
    return (
      <div flex bg-gradient-to-r from-fuchsia-200 to-indigo-200 w-full h-100vh>
        {<Bokeh/> for i in range(20)}

        <div flex justify-center w-full>
          <SettledCake />
          <div absolute bottom-350px align-center font-mono text-4xl text-indigo-400>
          Happy Birthday To You!
          </div>
        </div>
        <div id="fireworks" absolute z-100 bg-black w-full h-100vh></div>
      </div>
      <script>
        import { Fireworks } from "@/fireworks-js/index.es.js";
        const container = document.getElementById('fireworks');
        const option = {
            autoresize: false,
            hue: {
                min: 0,
                max: 213,
            },
            acceleration: 1.01,
            brightness: {
                min: 46,
                max: 100,
            },
            decay: {
                min: 0.002,
                max: 0.037,
            },
            delay: {
                min: 20, //47.74,
                max: 60, //76.77,
            },
            explosion: 4,
            flickering: 52.17,
            intensity: 15.75,
            friction: 1.01,
            gravity: 0.87,
            opacity: 0.3,
            particles: 49,
            traceLength: 2.27,
            traceSpeed: 5,
            rocketsPoint: {
                min: 50,
                max: 50,
            },
            lineWidth: {
                explosion: {
                    min: 3.66,
                    max: 6.88,
                },
                trace: {
                    min: 6.24,
                    max: 10.00,
                },
            },
            lineStyle: 'round',
        };
        const fireworks = new Fireworks(container, option);
        container.addEventListener('click', (event) => {
            fireworks.start();
            setTimeout(function() {
              const style = "opacity: 0; transition-property: opacity; transition-timing-function: cubic-bezier(0.4, 0, 0.2, 1); transition-duration: 2s;"
              container.setAttribute('style', style);

              setTimeout(function() {
                  fireworks.stop(true);
              }, 3000);
            }, 3000);
        });
      </script>
    )

if __name__ == '__main__':
    from fryhcs import render
    print("render HappyBirthday")
    print(render(HappyBirthday))
    print()
    print("render html")
    print(html(HappyBirthday, title="生日快乐"))
