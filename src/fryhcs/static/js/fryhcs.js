let activeEffectStack = [];

class Signal {
    constructor(rawValue) {
        this.rawValue = rawValue;
        this.effectSet = new Set();
    }

    addEffect(effect) {
        this.effectSet.add(effect);
    }

    removeEffect(effect) {
        this.effectSet.delete(effect);
    }

    hasEffect(effect) {
        return this.effectSet.has(effect);
    }

    peek() {
        return this.rawValue;
    }

    get value() {
        const len = activeEffectStack.length;
        if (len === 0) {
            return this.rawValue;
        }
        const currentEffect = activeEffectStack[len-1];
        if (!this.hasEffect(currentEffect)) {
            this.effectSet.add(currentEffect);
            currentEffect.addSignal(this);
        }
        return this.rawValue;
    }

    set value(rawValue) {
        if (this.rawValue !== rawValue) {
            this.rawValue = rawValue;
            const errs = [];
            for (const effect of this.effectSet) {
                try {
                    effect.callback();
                } catch (err) {
                    errs.push([effect, err]);
                }
            }
            if (errs.length > 0) {
                throw errs;
            }
        }
    }
}

function signal(rawValue) {
    return new Signal(rawValue);
}


class Effect {
    constructor(fn) {
        this.fn = fn;
        this.active = false;
        this.todispose = false;
        this.disposed = false;
        this.signalSet = new Set();
    }

    addSignal(signal) {
        this.signalSet.add(signal);
    }

    removeSignal(signal) {
        this.signalSet.delete(signal);
    }

    callback() {
        if (this.active === true || this.disposed === true) {
            return;
        }
        activeEffectStack.push(this);
        this.active = true;
        this.signalSet.clear();
        try {
            this.fn();
        } finally {
            this.active = false;
            activeEffectStack.pop();
            if (this.todispose) {
                this.dispose();
            }
        }
    }

    dispose() {
        if (this.disposed) {
            return;
        }
        if (this.active) {
            this.todispose = true;
            return;
        }
        for (const signal of this.signalSet) {
            signal.removeEffect(this);
        }
        this.signalSet.clear();
        this.todispose = false;
        this.disposed = true;
    }
}

function effect(fn) {
    const e = new Effect(fn);
    try {
        e.callback();
    } catch (err) {
        e.dispose();
        throw err;
    }
    return e.dispose.bind(e);
}


// Computed是一个特殊的Signal，也是一个特殊的Effect。
// * 对于依赖它的Effect或其他Computed，它是一个Signal，
//   自己的值变化后，通知依赖它的Effect和其他Computed;
// * 对于它所依赖的Signal或其他Computed，它是一个Effect，
//   依赖变更后，它要跟着变更；
class Computed {
    constructor(fn) {
        this.fn = fn;
        this.rawValue = undefined;
        this.active = false;
        this.todispose = false;
        this.disposed = false;
        this.effectSet = new Set();
        this.signalSet = new Set();
    }

    addEffect(effect) {
        this.effectSet.add(effect);
    }

    removeEffect(effect) {
        this.effectSet.delete(effect);
    }

    hasEffect(effect) {
        return this.effectSet.has(effect);
    }

    peek() {
        return this.rawValue;
    }

    get value() {
        this.rawValue = this.fn();
        const len = activeEffectStack.length;
        if (len === 0) {
            return this.rawValue;
        }
        const currentEffect = activeEffectStack[len-1];
        if (!this.hasEffect(currentEffect)) {
            this.effectSet.add(currentEffect);
            currentEffect.addSignal(this);
        }
        return this.rawValue;
    }

    addSignal(signal) {
        this.signalSet.add(signal);
    }

    removeSignal(signal) {
        this.signalSet.delete(signal);
    }

    callback() {
        if (this.active === true || this.disposed === true) {
            return;
        }
        activeEffectStack.push(this);
        this.active = true;
        this.signalSet.clear();
        let rawValue;
        try {
            rawValue = this.fn();
            if (rawValue != this.rawValue) {
                this.rawValue = rawValue;
                const errs = [];
                for (const effect of this.effectSet) {
                    try {
                        effect.callback();
                    } catch (err) {
                        errs.push([effect, err]);
                    }
                }
                if (errs.length > 0) {
                    throw errs;
                }
            }
        } finally {
            this.active = false;
            activeEffectStack.pop();
            if (this.todispose) {
                this.dispose();
            }
        }
    }

    dispose() {
        if (this.disposed) {
            return;
        }
        if (this.active) {
            this.todispose = true;
            return;
        }
        for (const signal of this.signalSet) {
            signal.removeEffect(this);
        }
        this.signalSet.clear();
        for (const effect of this.effectSet) {
            effect.removeSignal(this);
        }
        this.effectSet.clear();
        this.todispose = false;
        this.disposed = true;
    }
}

function computed(fn) {
    return new Computed(fn);
}


/*
** hydrate the DOM tree in the specified containerDOM using the components args
** containerDOM: container dom element
** components:   map of cid -> {fryid: cid, fryname: name, fryurl: url, fryargs: args, fryrefs: refs}
**               这里的每个component可以是普通对象，也可以是一个代表组件的script元素
**               水合时只要求其有fryid/fryname/fryurl/fryargs/fryrefs这几个属性即可。
**               第一次html全量水合时是script元素，动态加载的组件是普通对象。
*/
async function hydrate(containerDOM, components) {
    // 1. 收集cid列表
    let cids = [];
    for (const cid in components) {
        cids.push(parseInt(cid));
    }

    // 2. 收集所有*html元素*的ref/refall信息，设置到所在组件的script元素上
    const embedElements = containerDOM.querySelectorAll('[data-fryref]:not(script)');
    for (const element of embedElements) {
        const refs = element.dataset.fryref;
        for (const ref of refs.split(' ')) {
            const [name, cid] = ref.split('-');
            const scriptElement = components[cid];
            if (name.endsWith(':a')) {
                const rname = name.slice(0, -2);
                if (rname in scriptElement.fryargs) {
                    scriptElement.fryargs[rname].push(element);
                } else {
                    scriptElement.fryargs[rname] = [element];
                }
            } else {
                scriptElement.fryargs[name] = element;
            }
        }
    }

    // 3. 执行水合操作
    function doHydrate(script, embedValues) {
        const cid = script.fryid;
        const rootElement = containerDOM.querySelector(`[data-fryid~="${cid}"]:not(script)`);
        const prefix = '' + cid + '/';
        function handle(element) {
            if ('fryembed' in element.dataset) {
                const embeds = element.dataset.fryembed;
                for (const embed of embeds.split(' ')) {
                    if (!embed.startsWith(prefix)) {
                        continue;
                    }
                    const [embedId, atype, ...args] = embed.substr(prefix.length).split('-');
                    const index = parseInt(embedId);
                    const arg = args.join('-')
                    if (index >= embedValues.length) {
                        console.log("invalid embed id: ", embedId);
                        continue;
                    }
                    const value = embedValues[index];

                    if (atype === 'text') {
                        // 设置html文本时需要进行响应式处理
                        if ((value instanceof Signal) || (value instanceof Computed)) {
                            effect(() => element.textContent = value.value);
                        } else {
                            element.textContent = value;
                        }
                    } else if (atype === 'event') {
                        element.addEventListener(arg, value);
                    } else if (atype === 'attr') {
                        // 设置html元素属性值时需要进行响应式处理
                        if (value instanceof Signal || value instanceof Computed) {
                            effect(() => element.setAttribute(arg, value.value));
                        } else {
                            element.setAttribute(arg, value);
                        }
                    } else if (atype === 'object') {
                        // 设置对象属性时不使用effect，signal对象本身将传给js脚本
                        if (!('frydata' in element)) {
                            element.frydata = {};
                        }
                        element.frydata[arg] = value;
                    } else {
                        console.log("invalid attribute type: ", atype);
                    }
                }
            }
            for (const child of element.children) {
                handle(child);
            }
        }
        handle(rootElement);
    }

    // 3.1 组件元素排序，从后往前(从里往外)执行组件水合代码
    cids.sort((x,y)=>y-x);

    for (const cid of cids) {
        const scid = ''+cid;
        let comp = components[scid];
        // 3.2 收集本组件中所有*子组件元素*的ref对象和refall对象列表，设置到本组件的comp元素上
        for (const name in comp.fryrefs) {
            const value = comp.fryrefs[name];
            if (Array.isArray(value)) {
                comp.fryargs[name] = value.map(subid=>components[subid].fryobject);
            } else {
                comp.fryargs[name] = components[value].fryobject;
            }
        }

        // 3.3 执行本组件水合
        // 不是每个组件都有js脚本，纯服务端组件没有js脚本
        if (typeof comp.fryurl !== 'undefined') {
            const { hydrate } = await import(comp.fryurl);
            await hydrate(comp, doHydrate);
        }
    }
}


async function getRemote(url, cname, args) {
    const sargs = JSON.stringify(args);
    let fullurl = url;
    if (url.startsWith('/')) {
        fullurl = window.location.origin + url;
    }
    const loc = new URL(fullurl);
    loc.search = new URLSearchParams({name: cname, args: sargs}).toString();
    const response = await fetch(loc);
    const data = await response.json();
    if (data.code === 0) {
        let root = document.createElement('div');
        root.innerHTML = data.dom;
        await hydrate(root, data.components);
        return root.firstElementChild;
    }
}


async function postRemote(url, cname, args, csrftoken) {
    let fullurl = url;
    if (url.startsWith('/')) {
        fullurl = window.location.origin + url;
    }
    const sargs = JSON.stringify(args);
    const rdata = new FormData();
    rdata.append('name', cname);
    rdata.append('args', sargs);
    let postargs = {method: 'POST', body: rdata};
    if (csrftoken) {
        postargs.headers = {'X-CSRFToken': csrftoken};
        postargs.mode = 'same-origin';
    }
    const response = await fetch(fullurl, postargs);
    const data = await response.json();
    if (data.code === 0) {
        let root = document.createElement('div');
        root.innerHTML = data.dom;
        await hydrate(root, data.components);
        return root.firstElementChild;
    }
}


export {
    signal,
    effect,
    computed,
    hydrate,
    getRemote,
    postRemote,
}
