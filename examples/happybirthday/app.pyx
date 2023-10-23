from fryhcs import Element, html
from flask import Flask

app = Flask(__name__)

@app.get('/')
def index():
    return html(HappyBirthday, title="生日快乐~")

def HappyBirthday(props):
    return (
      <div bg-gradient-to-r from-fuchsia-300 to-indigo-300
        w-full h-100vh>
      </div>
    )
