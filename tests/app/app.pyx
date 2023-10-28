from fryhcs import html, Element
from flask import Flask

app = Flask(__name__)

def App(**props):
    initial_count = 20
    return <div>
             <h1 ref=(header) text-cyan-500 hover:text-cyan-600 text-center mt-100px>
               Hello FryHCS!
             </h1>
             <p text-indigo-600 text-center mt-9>
               Count:
               <span text-red-600>{initial_count}(count)</span>
             </p>
             <div flex w-full justify-center>
               <button
                 @click=(increment)
                 class="inline-flex items-center justify-center h-10 gap-2 px-5 text-sm font-medium tracking-wide text-white transition duration-300 rounded focus-visible:outline-none whitespace-nowrap bg-emerald-500 hover:bg-emerald-600 focus:bg-emerald-700 disabled:cursor-not-allowed disabled:border-emerald-300 disabled:bg-emerald-300 disabled:shadow-none">
                 Increment
               </button>
             </div>
           </div>
           <script header initial={initial_count}>
              import {signal} from "fryhcs"

              let count = signal(initial)

              function increment() {
                  count.value ++;
                  header.textContent = `Hello FryHCS(${count.value})`;
              }
           </script>

@app.get('/')
def index():
    return html(App, "Hello")
