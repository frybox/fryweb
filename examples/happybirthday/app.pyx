from fryhcs import Element, html
from flask import Flask

app = Flask(__name__)

@app.get('/')
def index():
    return html(HappyBirthday, title="生日快乐~")

def HappyBirthday(props):
    return (
      <div bg-gradient-to-r from-fuchsia-200 to-indigo-200
        w-full h-full>
        Hello world
      </div>
    )
