const dsfrInitialized = new Promise((resolve, reject) => {
    if (typeof window.dsfr === "function") {
        return resolve(window.dsfr)
    }

    function dsfrStart() {
        clearTimeout(timer)
        window.removeEventListener("dsfr.start", dsfrStart)
        requestAnimationFrame(() => resolve(window.dsfr))
    }

    const timer = setTimeout(() => {
        window.removeEventListener("dsfr.start", dsfrStart)
        reject(new Error("dsfr not initialized after 5s"))
    }, 5000)
    window.addEventListener("dsfr.start", dsfrStart)
})

dsfrInitialized.then(dsfr => {
    // Imports (kind of)
    const {
        core: {Instance, DisclosureEvent, CollapseSelector, Collapse},
        internals: {
            register,
            ns,
            dom: {uniqueId},
        },
    } = dsfr

    const WIDGET_IDENTIFIER = ns("treeselect")
    const MAIN_BUTTON = ns.selector("treeselect__button")
    const MAIN_COLLAPSE = ns.selector("treeselect__collapse")
    const GROUP_SELECTOR = ns.selector("treeselect__group")
    const WIDGET_WRAPPER_CLASS = `.${WIDGET_IDENTIFIER}__wrapper`
    const WIDGET_WRAPPER = `.${WIDGET_IDENTIFIER} > ${WIDGET_WRAPPER_CLASS}`
    const MAIN_DROPDOWN = `.${WIDGET_IDENTIFIER}__collapse`
    const WIDGET_GROUP = `${WIDGET_WRAPPER} .${WIDGET_IDENTIFIER}__group`

    /**
     * @property {HTMLElement} node
     */
    class SearchBar extends Instance {
        static SEARCH = ns.emission("treeselect-search", "change")
        static RETRIEVE = ns.emission("treeselect-search", "retrive")
        static FOCUS = ns.emission("treeselect-search", "focus")

        static get instanceClassName() {
            return "TreeselectSearchbar"
        }

        init() {
            /**
             * @type {Object<string, Object<string, EventListenerOrEventListenerObject>>}
             * @private
             */
            this._boundListeners = {
                '.fr-input[type="search"]': {
                    focus: this.onChange.bind(this),
                    input: this.onChange.bind(this),
                },
            }

            this._boundListenersForEach((el, type, listener) => el.addEventListener(type, listener))
            this.addDescent(this.constructor.RETRIEVE, () => {
                for (const it of this.node.querySelectorAll('.fr-input[type="search"]')) {
                    it.dispatchEvent(new Event("input"))
                }
            })
            this.addDescent(this.constructor.FOCUS, () => {
                for (const it of this.node.querySelectorAll('.fr-input[type="search"]')) {
                    setTimeout(() => requestAnimationFrame(() => it.focus()), 50)
                }
            })
        }

        onChange({target: {value}}) {
            this.ascend(this.constructor.SEARCH, value)
        }

        dispose() {
            this._boundListenersForEach((el, type, listener) => el.removeEventListener(type, listener))
        }

        /**
         * @param {function(el: Element, type: string, listener: EventListenerOrEventListenerObject)} callback
         * @private
         */
        _boundListenersForEach(callback) {
            Object.entries(this._boundListeners).forEach(([selector, events]) => {
                this.node.querySelectorAll(selector).forEach(el => {
                    Object.entries(events).forEach(([type, listener]) => {
                        callback(el, type, listener)
                    })
                })
            })
        }
    }

    class TreeselectCollapse extends Collapse {
        static get instanceClassName() {
            return "TreeselectCollapse"
        }

        constructor() {
            super()
            this._selector = MAIN_COLLAPSE
            this.disclosuresGroupInstanceClassName = undefined
            this.modifier = `${CollapseSelector.COLLAPSE}--${this.type.id}`
        }

        init() {
            if (this.id.trim() === "") {
                this.id = uniqueId("fr-treeselect-main")
            }
            this.node.id = this.id
            const buttton = this.element.parent.node.querySelector(MAIN_BUTTON)
            buttton?.setAttribute("aria-controls", this.id)
            buttton?.setAttribute("type", "button")
            buttton?.setAttribute("aria-expanded", "false")
            this.node.classList.add(ns("collapse"))
            super.init()
        }
    }

    class TreeselectGroupCollapse extends Collapse {
        static get instanceClassName() {
            return "TreeselectGroupCollapse"
        }

        init() {
            /** @type {HTMLElement} */
            const label = this.element.parent.node.querySelector(
                `& > .fr-treeselect__group-header .fr-label[aria-controls~="${this.id}"]`,
            )

            if (label !== null) {
                const labelText = label.textContent.trim()

                label.innerHTML = `<span class="fr-sr-only">${label.textContent}</span>`
                label.removeAttribute("aria-controls")
                label.parentElement.classList.add("fr-treeselect__group-selectable")
                label.parentElement.insertAdjacentHTML(
                    "beforeend",
                    this.selectableGroupsAccordionButton(this.id, labelText),
                )
            }
            super.init()
        }

        selectableGroupsAccordionButton(ariaControls, textContent) {
            return `<button type="button" class="fr-treeselect__group-button fr-accordion__btn" aria-expanded="false" aria-controls="${ariaControls}">
                <span class="fr-sr-only">Ouvrir la catégorie </span>${textContent}
            </button>`
        }
    }

    class TreeselectGroup extends Instance {
        static get instanceClassName() {
            return "TreeselectGroup"
        }

        init() {
            this.register(
                [
                    `${MAIN_DROPDOWN} ${GROUP_SELECTOR} > .fr-collapse`,
                    `${MAIN_DROPDOWN} ${GROUP_SELECTOR} *:not(${GROUP_SELECTOR}) > .fr-collapse`,
                ].join(","),
                TreeselectGroupCollapse,
            )
        }
    }

    class Treeselect extends Instance {
        static SEARCH = ns.event("search")

        static get instanceClassName() {
            return "Treeselect"
        }

        init() {
            this.register(`${MAIN_DROPDOWN} > .${WIDGET_IDENTIFIER}__head > .fr-search-bar`, SearchBar)

            this.addAscent(SearchBar.SEARCH, this.onSearch.bind(this))
            this.descend(SearchBar.RETRIEVE)

            this.listen(DisclosureEvent.DISCLOSE, this.onOpen.bind(this))

            this.register(`.${WIDGET_IDENTIFIER} ${MAIN_COLLAPSE}`, TreeselectCollapse)
            this.register(WIDGET_GROUP, TreeselectGroup)
        }

        onSearch(value) {
            this.dispatch(this.constructor.SEARCH, {search: value})
        }

        onOpen({target}) {
            if (target.classList.contains("fr-treeselect__collapse")) {
                this.descend(SearchBar.FOCUS)
            }
        }
    }

    register(`.${WIDGET_IDENTIFIER}`, Treeselect)
}, console.error)
