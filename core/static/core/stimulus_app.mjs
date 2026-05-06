import {Controller, Application as StimulusApp} from "Stimulus"

// Drop when adoption is 99%; see https://caniuse.com/wf-promise-withresolvers
if (typeof Promise.withResolvers !== "function") {
    Promise.withResolvers = function withResolvers() {
        let resolve, reject
        const promise = new Promise((res, rej) => {
            resolve = res
            reject = rej
        })
        return {promise, resolve, reject}
    }
}

async function dsfrDisclosePromise(dsfrDisclosable) {
    const {promise, resolve} = Promise.withResolvers()

    if (dsfrDisclosable.isDisclosed) {
        resolve()
        return promise
    }

    const cb = () =>
        requestAnimationFrame(() => {
            dsfrDisclosable.node.classList.remove("no-animate")
            resolve()
        })

    dsfrDisclosable.node.addEventListener("dsfr.disclose", cb)
    dsfrDisclosable.node.classList.add("no-animate")
    dsfrDisclosable.disclose()
    return promise.then(() => dsfrDisclosable.node.removeEventListener("dsfr.disclose", cb))
}

function escapeHTML(value) {
    return new Option(`${value}`).innerHTML
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

        while (this.queue.length > 0) {
            const promises = Object.values(this.active)
            if (promises.length <= this.poolSize) {
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

        await Promise.allSettled(Object.values(this.active))
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
        if (previous === undefined || !previous.includes(action)) {
            target.dataset.action = `${previous} ${action}`.trim()
        }
    }

    /** @param {Event} evt */
    onClose(evt) {
        evt.preventDefault()
        evt.stopPropagation()
        if (this.hideValue) {
            this.element.hidden = true
        } else {
            this.element.remove()
        }
    }
}

const Application = new StimulusApp()
/** @type {Promise<StimulusApp>} */
const applicationReady = Application.start().then(() => {
    Application.register("dismissable-alert", AlertController)
    return Application
})

applicationReady.then(() => {
    // Polyfill to support with-empty-placeholder pattern when browser doesn't support :has
    // Drop when :has() adoption is >99%: https://caniuse.com/css-has
    if (!CSS.supports("selector(:has([hidden]))")) {
        const PLACEHOLDER_CONTAINER_CLASS = "with-empty-placeholder"
        const PLACEHOLDER_HIDDEN_CLASS = "with-empty-placeholder--placeholder-hidden"

        /** @type {WeakMap<WeakKey, MutationObserver>} */
        const observers = new WeakMap()

        /** @param {HTMLElement} node */
        function observeNode(node) {
            if (observers.has(node)) {
                return
            }

            const mutationObserver = new MutationObserver(mutationList => {
                let recomputeVisibility = false
                for (const mut of mutationList) {
                    if (recomputeVisibility === true) break
                    for (const it of [mut.target, ...mut.addedNodes]) {
                        if (it instanceof HTMLElement && it.classList.contains("with-empty-placeholder--item")) {
                            recomputeVisibility = true
                            break
                        }
                    }
                }

                if (!recomputeVisibility) return

                const hasVisibleChildren =
                    node.querySelectorAll(".with-empty-placeholder--item:not(.fr-hidden, [hidden], [aria-hidden])")
                        .length > 0

                for (const placeholder of node.querySelectorAll(".with-empty-placeholder--placeholder")) {
                    if (hasVisibleChildren) {
                        placeholder.classList.add(PLACEHOLDER_HIDDEN_CLASS)
                    } else {
                        placeholder.classList.remove(PLACEHOLDER_HIDDEN_CLASS)
                    }
                }
            })
            mutationObserver.observe(node, {
                childList: true,
                subtree: true,
                attributeFilter: ["class", "hidden", "aria-hidden"],
            })
            observers.set(node, mutationObserver)
        }

        /** @param {HTMLElement} node */
        function unobserveNode(node) {
            if (observers.has(node)) {
                observers.get(node).disconnect()
                observers.delete(node)
            }
        }

        for (const node of document.querySelectorAll(`.${PLACEHOLDER_CONTAINER_CLASS}`)) {
            observeNode(node)
        }

        const observer = new MutationObserver(mutationList => {
            for (const mutation of mutationList) {
                for (const node of [mutation.target, ...mutation.addedNodes]) {
                    if (node instanceof HTMLElement) {
                        if (node.classList.contains(PLACEHOLDER_CONTAINER_CLASS)) {
                            observeNode(node)
                        } else {
                            unobserveNode(node)
                        }
                    }
                }
                for (const node of mutation.removedNodes) {
                    unobserveNode(node)
                }
            }
        })
        observer.observe(document, {
            childList: true,
            subtree: true,
            attributeFilter: ["class"],
        })
    }
})

const COMMON_EVENTS = Object.freeze({
    DOCUMENT_SUCCESS: "DOCUMENT_SUCCESS",
    ALL_DOCUMENTS_SUCCES: "ALL_DOCUMENTS_SUCCES",
    DOCUMENT_DELETE: "DOCUMENT_DELETE",
})

export {applicationReady, dsfrDisclosePromise, fetchPool, escapeHTML, COMMON_EVENTS}
