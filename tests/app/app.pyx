from fryhcs import html, Element
from flask import Flask

app = Flask(__name__)

def App(props):
    initial_count = 10
    return <div>
             <h1 text-cyan-500 hover:text-cyan-600 text-center mt-100px>
               Hello FryHCS!
             </h1>
             <p text-indigo-600 text-center mt-9>
               Count:
               <span text-red-600>{initial_count}(count)</span>
             </p>
             <div flex w-full justify-center>
               <button type="button" @click=(increment)
                 mt-9 px-2 rounded border
                 bg-indigo-400 hover:bg-indigo-600>
                 Increment
               </button>
             </div>

             <script initial={initial_count}>
                import {signal} from "fryhcs"

                count = signal(initial)

                function increment() {
                    count.value ++
                }
             </script>
           </div>

@app.get('/')
def index():
    return html(App, "Hello")