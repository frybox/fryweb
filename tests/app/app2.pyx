from fryhcs import html, Element
from flask import Flask

app = Flask(__name__)

def App(props):
    initial_count = 10
    return <div>
             <h1 text-cyan-500 hover:text-cyan-600 text-center mt-100px>
               Hello FryHCS!
             </h1>
             <p text-indigo-600 text-center mt-9>Count: {initial_count}</p>
           </div>

@app.get('/')
def index():
    return html(App, "Hello")
