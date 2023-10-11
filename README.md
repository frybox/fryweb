# fryhcs
A python library to generate HTML, Javascript and CSS, based on pyx file.

## Features
* Support pyx extension to normal py file, similar to jsx, html tags can be written directly in py files.
* Provide a pyx file loader for python import machanism, pyx files can be loaded and executed by CPython directly.
* Provide a utility first css framework, similar to TailwindCSS, support attributify mode similar to WindiCSS
* Can be used with django/flask framework.
* Provide a command line tool `fry` based on flask. 
* Provide development server which support server auto reload and browser auto reload when file saved.

All features are implemented in python, no node ecosystem is required.

## Installation

```bash
pip install fryhcs
```

## Usage

create app.pyx file:

```python
from fryhcs import html, Element
from flask import Flask

app = Flask(__name__)

def App(props):
    return <h1>Hello FryHCS!</h1>

@app.get('/')
def index():
    return html(App, "Hello")
```

in the same directory as app.pyx, run command:

```bash
fry run --debug
```

open browser, access `http://127.0.0.1:5000`

## License
MIT License

