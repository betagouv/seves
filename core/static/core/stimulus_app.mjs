import {Application as StimulusApp, Controller} from "Stimulus";

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

class FetchPool {
    static createFetchPool() {
        const instance = new FetchPool()
        return instance.fetchPool.bind(instance)
    }

    constructor() {
        this.poolSize = 4
        this.ids = [...Array(this.poolSize + 1).keys()]
        /** @type {(function(): Promise<void>)[]} */
        this.queue = []
        /** @type {Object<Number, Promise<void>>}*/
        this.active = {}
        this.current = Promise.resolve()
    }

    async enqueue(func) {
        this.queue.push(func)

        while(this.queue.length > 0) {
            const promises = Object.values(this.active)
            if(promises.length <= this.poolSize) {
                const func = this.queue.shift()
                const nextId = this.ids.pop()
                this.active[nextId] = func().finally(() => {
                    delete this.active[nextId]
                    this.ids.push(nextId)
                })
            } else {
                await Promise.race(promises)
            }
        }

        await Promise.allSettled(Object.values(this.active));
    }

    fetchPool(input, init) {
        const {promise, resolve, reject} = Promise.withResolvers()
        this.enqueue(async () => fetch(input, init).then(resolve, reject))
        return promise
    }
}


/**
 * @param {RequestInfo | URL} input
 * @param {RequestInit | undefined} init
 * @return {Promise<Response>}
 */
const fetchPool = FetchPool.createFetchPool()

/**
 * @property {HTMLElement} element
 * @property {Boolean} hideValue
 * @property {HTMLElement} closeTarget
 */
class AlertController extends Controller {
    static values = {hide: {type: Boolean, default: false}}
    static targets = ["close"]

    /**@param {HTMLElement} target */
    closeTargetConnected(target) {
        const action = `click->${this.identifier}#onClose`
        const previous = target.dataset.action
        if(previous === undefined || !previous.includes(action)) {
            target.dataset.action = `${previous} ${action}`.trim()
        }
    }

    /** @param {Event} evt */
    onClose(evt) {
        evt.preventDefault()
        evt.stopPropagation()
        if(this.hideValue) {
            this.element.hidden = true
        } else {
            this.element.remove()
        }
    }
}

const Application = new StimulusApp();
/** @type {Promise<StimulusApp>} */
const applicationReady = Application.start().then(() => {
    Application.register("dismissable-alert", AlertController)
    return Application
})

export {applicationReady, dsfrDisclosePromise, fetchPool}
