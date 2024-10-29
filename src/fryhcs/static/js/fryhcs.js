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
** hydrate the DOM tree in the specified domContainer using the components args
** domContainer: container dom element
** components:   map of cid -> {fryid, fryname, fryurl, fryargs, fryrefs}
**               fryid: 组件id
**               fryname: 组件名
**               fryurl: 组件js文件的url
**               fryargs: 组件js prepare代码执行时的(部分)参数，另一部分是refs
**               fryrefs：子组件元素的ref/refall数据
**               components值为空时，将根据domContainer中的组件ID，从dom的组件script
**               元素取相关组件信息。
*/
async function hydrate(domContainer, components) {
    // 0. 如果没有传组件列表过来，遍历整个dom树，查找所有
    if (!components) {
        components = {};
        const scripts = {};
        for (const script of document.querySelectorAll('script[data-fryid]')) {
            scripts[script.dataset.fryid] = script;
        }
        function collect(element) {
            if (element.tagName === 'SCRIPT') {
                // 对于脚本，无需处理
                return;
            } else if (element.tagName === 'TEMPLATE') {
                // 组件渲染期间，不会使用到组件内部模板中的组件信息
                return;
            } else {
                // 对于有data-fryid属性的其他元素，根据对应id的script元素内容初始化component对象
                if (element.dataset && 'fryid' in element.dataset) {
                    for (const cid of element.dataset.fryid.split(' ')) {
                        if (cid in components) {
                            throw `duplicate component id ${cid}`;
                        }
                        if (!(cid in scripts)) {
                            throw `unknown component id ${cid}`;
                        }
                        const script = scripts[cid];
                        const data = JSON.parse(script.textContent);
                        components[cid] = {
                            fryid: cid,
                            fryname: script.dataset.fryname,
                            fryurl: script.dataset.fryurl,
                            fryargs: data.args,
                            fryrefs: data.refs,
                        }
                    }
                }
                // 然后处理孩子元素
                for (const child of element.children) {
                    collect(child);
                }
            }
        }
        collect(domContainer);
    }

    // 1. 收集cid列表
    let cids = [];
    for (const cid in components) {
        cids.push(parseInt(cid));
    }

    // 2. 收集所有*html元素*的ref/refall信息，设置到所在组件的script元素上
    const embedElements = domContainer.querySelectorAll('[data-fryref]:not(script)');
    for (const element of embedElements) {
        const refs = element.dataset.fryref;
        for (const ref of refs.split(' ')) {
            const [name, cid] = ref.split('-');
            const component = components[cid];
            if (name.endsWith(':a')) {
                const rname = name.slice(0, -2);
                if (rname in component.fryargs) {
                    component.fryargs[rname].push(element);
                } else {
                    component.fryargs[rname] = [element];
                }
            } else {
                component.fryargs[name] = element;
            }
        }
    }

    // 对一个组件执行水合操作
    function doHydrate(component) {
        const domElement = component.domElement;
        const prefix = '' + component.fryid + '/';
        const embedValues = component.fryembeds;
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
                        // 该功能已弃用，暂时保留代码
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
        handle(domElement);
    }

    // 3. 组件元素排序，从后往前(从里往外)执行组件水合代码
    cids.sort((x,y)=>y-x);

    // 4. 按照从里到外的顺序分别对每个组件执行水合
    for (const cid of cids) {
        const scid = ''+cid;
        const comp = components[scid];
        const domElement = domContainer.querySelector(`[data-fryid~="${scid}"]:not(script)`);

        // 4.1 如果没找到该组件对应的dom元素（可能在template中，也可能不在domContainer子树范围内），
        //     没有水合对象，继续下一个组件
        if (!domElement) { continue; }

        // 4.2 在dom元素和组件实例对象之间建立关联
        comp.domElement = domElement;
        if (!('fryComponents' in domElement)) {
            domElement.fryComponents = [comp];
        } else {
            domElement.fryComponents.unshift(comp);
        }

        // 4.3 如果该组件是纯服务端组件，没有对应的前端逻辑，无需水合，继续下一个组件
        if (typeof comp.fryurl === 'undefined') { continue; }

        // 4.4 收集本组件中所有*子组件元素*的ref对象和refall对象列表，设置到本组件的参数列表中
        // 4.4.1 子组件模板的对象需要特殊处理，返回包含模板和实例化函数的对象
        function templator(subid) {
            const template = domContainer.querySelector(`[data-frytid="${subid}"]`);
            const generate = async () => {
                let clone = template.content.cloneNode(true);
                await hydrate(clone);
                return clone.firstElementChild.fryComponents[0];
            };
            return { template, generate };
        }
        // 4.4.2 对于每个引用，单独进行处理
        for (const name in comp.fryrefs) {
            const value = comp.fryrefs[name];
            let rname = name;
            let f = (subid) => components[subid];
            if (name.startsWith('t:')) {
                rname = name.slice(2);
                f = templator;
            }
            if (Array.isArray(value)) {
                comp.fryargs[rname] = value.map(subid=>f(subid));
            } else {
                comp.fryargs[rname] = f(value);
            }
        }

        // 4.5 执行本组件水合
        const { prepare } = await import(comp.fryurl);
        await prepare(comp);
        doHydrate(comp);
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
