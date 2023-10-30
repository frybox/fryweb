# Fryhcs
A Python library to generate HTML, Javascript and CSS, based on .fy file.

Fy is jsx in python, it's the core of this project.

Fryhcs is heavily inspired by React JSX, TailwindCSS, WindiCSS in JS ecosystem.

**FRY** **H**tml, **C**ss and Java**S**cript, in pure Python, no nodejs-based tooling needed!

## Features
* Support fy extension to normal python file, similar to jsx, write html tags in python file.
* Provide a fy loader for python import machanism, load and execute fy files directly.
* Provide a utility-first css framework, similar to TailwindCSS, support attributify mode similar to WindiCSS.
* Support django/flask framework.
* Provide pygments lexer for fy.
* Provide development server which supports server/browser auto reloading when file saved.
* Provide a command line tool `fry`, build css/js, highlight and run fy file and run development server. 
* Support plugin machanism, anyone can extends with her/his own custom css utilities.

All features are implemented in pure Python, no node.js ecosystem is required.

## Installation

```bash
$ pip install fryhcs
```

## Usage

### 1. Basic
create app.fy file:

```python
from fryhcs import html, Element
from flask import Flask

app = Flask(__name__)

def App(**props):
    return <h1 text-cyan-500 hover:text-cyan-600 text-center mt-100px>
             Hello FryHCS!
           </h1>

@app.get('/')
def index():
    return html(App, "Hello")
```

in the same directory as app.fy, run command:

```bash
$ fry x2y app.fy
```

check the generated python content:

```python
from fryhcs import html, Element
from flask import Flask

app = Flask(__name__)

def App(**props):
    return Element("h1", {"class": "text-cyan-500 hover:text-cyan-600 text-center mt-100px", "children": ["Hello FryHCS!"]})

@app.get('/')
def index():
    return html(App, "Hello")

```

To generate CSS file `static/css/styles.css`, run command:
```bash
$ fry x2css app.fy
```

Generated CSS:

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
$ fry serve --debug
```

Open browser, access `http://127.0.0.1:5000` to browse the page.

Change the app.fy file, save, check the browser auto reloading.

`fryhcs.render` can be used to render component directly.

Create components.fy and input following code:

```python
from fryhcs import Element

def Component(**props):
    return <h1 text-cyan-500 hover:text-cyan-600 text-center mt-100px>
             Hello FryHCS!
           </h1>

if __name__ == '__main__':
    from fryhcs import render
    print(render(Component))
```

Run command to see the generated html fragment:
```bash
$ fry run component.fy
```


### 2. Using python variable in html markup:

```python
from fryhcs import html, Element
from flask import Flask

app = Flask(__name__)

def App(**props):
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

def App(**props):
    initial_count = 10
    return Element("div", {"children": [Element("h1", {"class": "text-cyan-500 hover:text-cyan-600 text-center mt-100px", "children": ["Hello FryHCS!"]}), Element("p", {"class": "text-indigo-600 text-center mt-9", "children": ["Count:", (initial_count)]})]})

@app.get('/')
def index():
    return html(App, "Hello")

```

### 3. Add js logic and reactive variable(signal):

```python
from fryhcs import html, Element
from flask import Flask

app = Flask(__name__)

def App(**props):
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
           </div>
           <script initial={initial_count}>
              import {signal} from "fryhcs"

              count = signal(initial)

              function increment() {
                  count.value ++
              }
           </script>

@app.get('/')
def index():
    return html(App, "Hello")
```

Generated python:

```python
from fryhcs import html, Element
from flask import Flask

app = Flask(__name__)

def App(**props):
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
    const {hydrate: hydrate$$, collectrefs: collectrefs$$} = await import("fryhcs");
    const rootElement$$ = script$$.parentElement;
    const componentId$$ = script$$.dataset.fryid;
    collectrefs$$(rootElement$$, script$$, componentId$$);
    const initial = ("frydata" in script$$ && "initial" in script$$.frydata) ? script$$.frydata.initial : script$$.dataset.initial;

                const {signal} = await import("fryhcs")

                count = signal(initial)

                function increment() {
                    count.value ++
                }

    let embeds$$ = [count, increment];
    hydrate$$(rootElement$$, componentId$$, embeds$$);
}]);

```

Generated HTML:

```html
<!DOCTYPE html>
<html lang=en>
    <head>
        <meta charset="utf-8">
        <title>Hello</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link rel="stylesheet" href="/static/css/styles.css">
        <script type="importmap">

      {
        "imports": {
          "fryhcs": "/static/js/fryhcs.js",
          "components/": "/static/js/components/",
          "@/": "/static/"
        }
      }

        </script>
    </head>
    <body>
        <div data-fryclass="app:App" data-fryid="1">
            <script src="/static/js/components/db9292e32031f3a02ee988097c493ef49696927e.js" data-fryid="1" data-initial="10"></script>
            <h1 class="text-cyan-500 hover:text-cyan-600 text-center mt-100px">Hello FryHCS!</h1>
            <p class="text-indigo-600 text-center mt-9">
                Count:
                <span class="text-red-600">
                    <span data-fryembed="1/0-text">10</span>
                </span>
            </p>
            <div class="flex w-full justify-center">
                <button type="button" class="mt-9 px-2 rounded border bg-indigo-400 hover:bg-indigo-600" data-fryembed="1/1-event-click">Increment</button>
            </div>
        </div>
        <script>
            (async function() {
                if ('fryfunctions$$'in window) {
                    for (const [script,fn] of window.fryfunctions$$) {
                        await fn(script);
                    }
                }
            }
            )();
        </script>
    </body>
</html>
```

## Command Line Tool `fry`

## Configuration

## Django Integration

## Flask Integration

## License
MIT License

## FAQ
### 1. Why named fryhcs
**FRY** **H**tml, **C**ss and Java**S**cript, in pure Python, no nodejs-based tooling needed!

In fact, this project is created by the father of one son(**F**ang**R**ui) and one daughter(**F**ang**Y**i)...

### 2. Why name the file format .fy
Originally, the file format is named .pyx, just similar to famous React jsx. But .pyx is already
used in Cython, so it has to be renamed.

### 3. Is it good to merge frontend code and backend code into one file?
Good question. We always say frontend-backend separation. But logically, for a web app, the
frontend code is usually tightly coupled with the backend code, although they are running on
different platform, at different place. When we change one function, usually we should change
backend logic and frontend logic together, from diffent files.

web app code should be separated by logic, not by the deployment and running place. We can use
building tools to separate code for different place.

### 4. Why not use the major tooling based on nodejs to handle frontend code?
Ok, there's too many tools! For me, as a backend developer, I always feel the frontend tools are
too complex, gulp, grunt, browsify, webpack, vite, postcss, tailwind, esbuild, rollup..., with too
many configuration files.

Yes, npm registy is a great frontend ecosystem, pypi is a great backend ecosystem. I need them,
but I only need the great libraries in these two great ecosystems, not soooo many different tools.
so one command `fry` is enough, it can be used to generate html, css, javascript, and handle
the downloading of javascript libraries from npm registry (soon).
