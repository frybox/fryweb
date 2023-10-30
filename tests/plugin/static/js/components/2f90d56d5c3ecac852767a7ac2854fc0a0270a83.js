import {hydrate as hydrate$$} from "fryhcs";
export const hydrate = async function (script$$) {
    const rootElement$$ = script$$.parentElement;
    const componentId$$ = script$$.dataset.fryid;
    const initial = ("frydata" in script$$ && "initial" in script$$.frydata) ? script$$.frydata.initial : script$$.dataset.initial;
    
              const {signal} = await import("fryhcs");

              let count = signal(initial);

              function increment() {
                  count.value ++;
              }
           
    let embeds$$ = [count, increment];
    hydrate$$(rootElement$$, componentId$$, embeds$$);
};
