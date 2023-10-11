from fryhcs import html, Element
from flask import Flask

app = Flask(__name__)

def App(props):
    return <h1 text-cyan-500 text-center mt-100px hover:text-cyan-600>
             Hello FryHCS!
           </h1>

@app.get('/')
def index():
    return html(App, "Hello")
