import {Application as StimulusApp} from "Stimulus";

// Drop when adoption is 99%; see https://caniuse.com/wf-promise-withresolvers
if(typeof Promise.withResolvers !== "function") {
    Promise.withResolvers = function withResolvers() {
        let resolve, reject;
        const promise = new Promise((res, rej) => {
            resolve = res;
            reject = rej;
        });
        return {promise, resolve, reject}
    }
}

async function dsfrDisclosePromise(dsfrDisclosable) {
    const {promise, resolve} = Promise.withResolvers()

    if(dsfrDisclosable.isDisclosed) {
        resolve()
        return promise
    }

    const cb = () => requestAnimationFrame(() => {
        dsfrDisclosable.node.classList.remove("no-animate")
        resolve()
    })

    dsfrDisclosable.node.addEventListener("dsfr.disclose", cb)
    dsfrDisclosable.node.classList.add("no-animate")
    dsfrDisclosable.disclose()
    return promise.then(() => dsfrDisclosable.node.removeEventListener("dsfr.disclose", cb))
}

const Application = new StimulusApp();
/** @type {Promise<StimulusApp>} */
const applicationReady = Application.start().then(() => Application)

export {applicationReady, dsfrDisclosePromise}
