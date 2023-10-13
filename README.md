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
$ pip install fryhcs
```

## Usage

### Basic
create app.pyx file:

```python
from fryhcs import html, Element
from flask import Flask

app = Flask(__name__)

def App(props):
    return <h1 text-cyan-500 hover:text-cyan-600 text-center mt-100px>
             Hello FryHCS!
           </h1>

@app.get('/')
def index():
    return html(App, "Hello")
```

in the same directory as app.pyx, run command:

```bash
$ fry x2y app.pyx
```

check the generated python content:

```python
from fryhcs import html, Element
from flask import Flask

app = Flask(__name__)

def App(props):
    return Element("h1", {"class": "text-cyan-500 hover:text-cyan-600 text-center mt-100px", "children": ["Hello FryHCS!"]})

@app.get('/')
def index():
    return html(App, "Hello")

```

Generated CSS file `static/css/styles.css`:

```css
....

.text-cyan-500 {
  color: rgb(6 182 212);
}

.text-center {
  text-align: center;
}

.mt-100px {
  margin-top: 100px;
}

.hover\:text-cyan-600:hover {
  color: rgb(8 145 178);
}

```

To serve this app, run command:

```bash
$ fry run --debug
```

Open browser, access `http://127.0.0.1:5000` to browse the page.

Change the app.pyx file, save, check the browser auto reloading.

### Using python variable in html markup:

```python
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
```

Generated python:

```python
from fryhcs import html, Element
from flask import Flask

app = Flask(__name__)

def App(props):
    initial_count = 10
    return Element("div", {"children": [Element("h1", {"class": "text-cyan-500 hover:text-cyan-600 text-center mt-100px", "children": ["Hello FryHCS!"]}), Element("p", {"class": "text-indigo-600 text-center mt-9", "children": ["Count:", (initial_count)]})]})

@app.get('/')
def index():
    return html(App, "Hello")

```

### Add js login and reactive variable:

```python
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
```

Generated python:

```python
from fryhcs import html, Element
from flask import Flask

app = Flask(__name__)

def App(props):
    initial_count = 10
    return Element("div", {"call-client-script": ["db9292e32031f3a02ee988097c493ef49696927e", [("initial", (initial_count))]], "children": [Element("h1", {"class": "text-cyan-500 hover:text-cyan-600 text-center mt-100px", "children": ["Hello FryHCS!"]}), Element("p", {"class": "text-indigo-600 text-center mt-9", "children": ["Count:", Element("span", {"class": "text-red-600", "children": [Element("span", {"*": Element.ClientEmbed(0), "children": [(initial_count)]})]})]}), Element("div", {"class": "flex w-full justify-center", "children": [Element("button", {"type": "button", "@click": Element.ClientEmbed(1), "class": "mt-9 px-2 rounded border bg-indigo-400 hover:bg-indigo-600", "children": ["Increment"]})]})]})

@app.get('/')
def index():
    return html(App, "Hello")
```

Generated js script `static/js/components/db9292e32031f3a02ee988097c493ef49696927e.js`:

```js
'fryfunctions$$' in window || (window.fryfunctions$$ = []);
window.fryfunctions$$.push([document.currentScript, async function (script$$) {
    const initial = ("frydata" in script$$ && "initial" in script$$.frydata) ? script$$.frydata.initial : script$$.dataset.initial;

                const {signal} = await import("fryhcs")

                count = signal(initial)

                function increment() {
                    count.value ++
                }

    const {hydrate: hydrate$$} = await import("fryhcs");
    const rootElement$$ = script$$.parentElement;
    const componentId$$ = script$$.dataset.fryid;
    let embeds$$ = [count, increment];
    hydrate$$(rootElement$$, componentId$$, embeds$$);
}]);

```

## License
MIT License

