# Fryhcs
A Python library to generate HTML, Javascript and CSS, based on .fry file.

Fry is jsx in python, it's the core of this project.

Fryhcs is heavily inspired by React JSX, TailwindCSS, WindiCSS in JS ecosystem.

**FRY** **H**tml, **C**ss and Java**S**cript, in pure Python, no nodejs-based tooling needed!

## Features
* Support fry extension to normal python file, similar to jsx, write html tags in python file.
* Provide a fry loader for python import machanism, load and execute .fry files directly by CPython.
* Provide a utility-first css framework, similar to TailwindCSS, support attributify mode similar to WindiCSS.
* Support django/flask framework.
* Provide pygments lexer for fry.
* Provide a development server which supports server/browser auto reloading when file saved.
* Provide a command line tool `fry`, build css/js, highlight and run fry file and run development server. 
* Support plugin machanism, anyone can extends with her/his own custom css utilities.

All features are implemented in pure Python, no node.js ecosystem is required.

## Installation

```bash
$ pip install fryhcs
```

## Usage

### 1. Basic
create app.fry file:

```python
from fryhcs import html, Element
from flask import Flask

app = Flask(__name__)

def App():
    <template>
      <h1 text-cyan-500 hover:text-cyan-600 text-center mt-100px>
        Hello FryHCS!
      </h1>
    </template>

@app.get('/')
def index():
    return html(App, "Hello")
```

in the same directory as app.fry, run command:

```bash
$ fry topy app.fry
```

check the generated python content:

```python
from fryhcs import html, Element
from flask import Flask

app = Flask(__name__)

def App():
    return Element("h1", {"class": "text-cyan-500 hover:text-cyan-600 text-center mt-100px", "children": ["Hello FryHCS!"]})

@app.get('/')
def index():
    return html(App, "Hello")

```

To generate CSS file `static/css/styles.css`, run command:
```bash
$ fry tocss app.fry
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
$ fry dev 
```

Open browser, access `http://127.0.0.1:5000` to browse the page.

Change the app.fry file, save, check the browser auto reloading.

`fryhcs.render` can be used to render component directly.

Create components.fry and input following code:

```python
from fryhcs import Element

def Component(**props):
    <template>
      <h1 text-cyan-500 hover:text-cyan-600 text-center mt-100px>
        Hello FryHCS!
      </h1>
    </template>

if __name__ == '__main__':
    from fryhcs import render
    print(render(Component))
```

Run command to see the generated html fragment:
```bash
$ fry run component.fry
```


### 2. Using python variable in html markup:

```python
from fryhcs import html, Element
from flask import Flask

app = Flask(__name__)

def App():
    initial_count = 10

    <template>
      <div>
        <h1 text-cyan-500 hover:text-cyan-600 text-center mt-100px>
          Hello FryHCS!
        </h1>
        <p text-indigo-600 text-center mt-9>Count: {initial_count}</p>
      </div>
    </template>

@app.get('/')
def index():
    return html(App, "Hello")
```

Generated python:

```python
from fryhcs import html, Element
from flask import Flask

app = Flask(__name__)

def App():
    initial_count = 10
    return Element("div", {"children": [Element("h1", {"class": "text-cyan-500 hover:text-cyan-600 text-center mt-100px", "children": ["Hello FryHCS!"]}), Element("p", {"class": "text-indigo-600 text-center mt-9", "children": ["Count:", (initial_count)]})]})

@app.get('/')
def index():
    return html(App, "Hello")

```

### 3. Add js logic and reactive variable(signal/computed):

```python
from fryhcs import html, Element
from flask import Flask

app = Flask(__name__)

def App():
    initial_count = 20

    <template>
       <div>
         <h1 ref=(header) text-cyan-500 hover:text-cyan-600 text-center mt-100px>
           Hello FryHCS!
         </h1>
         <p text-indigo-600 text-center mt-9>
           Count:
           <span text-red-600>[{initial_count}](count)</span>
         </p>
         <p text-indigo-600 text-center mt-9>
           Double:
           <span text-red-600>[{initial_count*2}](doubleCount)</span>
         </p>
         <div flex w-full justify-center>
           <button
             @click=(increment)
             class="inline-flex items-center justify-center h-10 gap-2 px-5 text-sm font-medium tracking-wide text-white transition duration-300 rounded focus-visible:outline-none whitespace-nowrap bg-emerald-500 hover:bg-emerald-600 focus:bg-emerald-700 disabled:cursor-not-allowed disabled:border-emerald-300 disabled:bg-emerald-300 disabled:shadow-none">
             Increment
           </button>
         </div>
       </div>
    </template>

    <script initial={initial_count}>
       import {signal, computed} from "fryhcs"
 
       let count = signal(initial)
 
       let doubleCount = computed(()=>count.value*2)
 
       function increment() {
           count.value ++;
           header.textContent = `Hello FryHCS(${count.value})`;
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

def App():
    initial_count = 20

    return Element("div", {"call-client-script": ["App-1171022438ea1f5e3d31f5fb191ca3c18adfda49", [("initial", (initial_count))]], "children": [Element("h1", {"ref:header": Element.ClientEmbed(0), "class": "text-cyan-500 hover:text-cyan-600 text-center mt-100px", "children": ["Hello FryHCS!"]}), Element("p", {"class": "text-indigo-600 text-center mt-9", "children": ["Count:", Element("span", {"class": "text-red-600", "children": [Element("span", {"*": Element.ClientEmbed(1), "children": [f"""{initial_count}"""]})]})]}), Element("p", {"class": "text-indigo-600 text-center mt-9", "children": ["Double:", Element("span", {"class": "text-red-600", "children": [Element("span", {"*": Element.ClientEmbed(2), "children": [f"""{initial_count*2}"""]})]})]}), Element("div", {"class": "flex w-full justify-center", "children": [Element("button", {"@click": Element.ClientEmbed(3), "class": "inline-flex items-center justify-center h-10 gap-2 px-5 text-sm font-medium tracking-wide text-white transition duration-300 rounded focus-visible:outline-none whitespace-nowrap bg-emerald-500 hover:bg-emerald-600 focus:bg-emerald-700 disabled:cursor-not-allowed disabled:border-emerald-300 disabled:bg-emerald-300 disabled:shadow-none", "children": ["Increment"]})]})]})


@app.get('/')
def index():
    return html(App, "Hello")
```

Generated js script `static/js/components/.tmp/App-1171022438ea1f5e3d31f5fb191ca3c18adfda49.js`:

```js
export { hydrate as hydrateAll } from "fryhcs";
export const hydrate = async function (element$$, doHydrate$$) {
    const { header, initial } = element$$.fryargs;

              const {signal, computed} = await import("fryhcs")

              let count = signal(initial)

              let doubleCount = computed(()=>count.value*2)

              function increment() {
                  count.value ++;
                  header.textContent = `Hello FryHCS(${count.value})`;
              }

    const embeds$$ = [header, count, doubleCount, increment];
    doHydrate$$(element$$, embeds$$);
};
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
  </head>
  <body>
    <div><script data-fryid="1" data-fryclass="app:App" data-initial="20"></script><h1 class="text-cyan-500 hover:text-cyan-600 text-center mt-100px" data-fryembed="1/0-ref-header">Hello FryHCS!</h1><p class="text-indigo-600 text-center mt-9">Count:<span class="text-red-600"><span data-fryembed="1/1-text">20</span></span></p><p class="text-indigo-600 text-center mt-9">Double:<span class="text-red-600"><span data-fryembed="1/2-text">40</span></span></p><div class="flex w-full justify-center"><button class="inline-flex items-center justify-center h-10 gap-2 px-5 text-sm font-medium tracking-wide text-white transition duration-300 rounded focus-visible:outline-none whitespace-nowrap bg-emerald-500 hover:bg-emerald-600 focus:bg-emerald-700 disabled:cursor-not-allowed disabled:border-emerald-300 disabled:bg-emerald-300 disabled:shadow-none" data-fryembed="1/3-event-click">Increment</button></div></div>

    <script type="module">
      let hydrates = {};
      import { hydrate as hydrate_0, hydrateAll } from '/static/js/components/1171022438ea1f5e3d31f5fb191ca3c18adfda49.js';
      hydrates['1'] = hydrate_0;
      await hydrateAll(hydrates);
    </script>

  <script type="module">
    let serverId = null;
    let eventSource = null;
    let timeoutId = null;
    function checkAutoReload() {
        if (timeoutId !== null) clearTimeout(timeoutId);
        timeoutId = setTimeout(checkAutoReload, 1000);
        if (eventSource !== null) eventSource.close();
        eventSource = new EventSource("/_check_hotreload");
        eventSource.addEventListener('open', () => {
            console.log(new Date(), "Auto reload connected.");
            if (timeoutId !== null) clearTimeout(timeoutId);
            timeoutId = setTimeout(checkAutoReload, 1000);
        });
        eventSource.addEventListener('message', (event) => {
            const data = JSON.parse(event.data);
            if (serverId === null) {
                serverId = data.serverId;
            } else if (serverId !== data.serverId) {
                if (eventSource !== null) eventSource.close();
                if (timeoutId !== null) clearTimeout(timeoutId);
                location.reload();
                return;
            }
            if (timeoutId !== null) clearTimeout(timeoutId);
            timeoutId = setTimeout(checkAutoReload, 1000);
        });
    }
    checkAutoReload();
  </script>

  </body>
</html>
```

### 4. Reference html element and component element in js logic:

```python
from fryhcs import Element, html
from flask import Flask

app = Flask(__name__)

@app.get('/')
def index():
    return html(RefApp, title="test ref")

def Refed():
    <template>
      <div>
        hello world
      </div>
    </template>
    <script>
      export default {
          hello() {
              console.log('hello hello')
          }
      }
    </script>

def RefApp():

    <template>
      <div w-full h-100vh flex flex-col gap-y-10 justify-center items-center>
        <p ref=(foo) text-indigo-600 text-6xl transition-transform duration-1500>
          Hello World!
        </p>
        <p ref=(bar) text-cyan-600 text-6xl transition-transform duration-1500>
          Hello FryHCS!
        </p>
        {<p refall=(foobar)>foobar</p> for i in range(3)}
        <Refed ref=(refed) refall=(refeds)/>
        {<Refed refall=(refeds) /> for i in range(2)}
      </div>
    </template>

    <script foo bar foobar refed refeds>
      setTimeout(()=>{
        foo.style.transform = "skewY(180deg)";
      }, 1000);
      setTimeout(()=>{
        bar.style.transform = "skewY(180deg)";
      }, 2500);
      for (const fb of foobar) {
        console.log(fb);
      }
      refed.hello()
      for (const r of refeds) {
          r.hello()
      }
    </script>

if __name__ == '__main__':
    print(html(RefApp))
```

## Command Line Tool `fry`

## Configuration

## Django Integration

## Flask Integration

## FastAPI Integration


## License
MIT License

## Road Map
* [ ] support component fetch from backend
* [ ] support component CRUD from frontend
* [ ] support multiple UI design systems


## FAQ
### 1. Why named fryhcs
**FRY** **H**tml, **C**ss and Java**S**cript, in pure Python, no nodejs-based tooling needed!

In fact, this project is created by the father of one boy(**F**ang**R**ui) and one girl(**F**ang**Y**i)...

### 2. Why is the file format named to be .fry
Originally, the file format is named .pyx, just similar to famous React jsx. But .pyx is already
used in Cython, so it has to be renamed.

First it's renamed to be .fy, easy to write. Unfortunately, .fy is also used by a rubyvm-based
language called fancy. But from [rubygems][1] and [github][2], there's no activity for ten years
on this project, and the last version is 0.10.0.

At last, it's named to be .fry.

[1]: https://rubygems.org/gems/fancy
[2]: https://github.com/bakkdoor/fancy

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
