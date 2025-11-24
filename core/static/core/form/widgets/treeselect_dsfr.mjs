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
        core: {Instance, DisclosureEvent},
        internals: {
            register,
            ns,
            dom: {uniqueId},
        },
    } = dsfr

    const WIDGET_IDENTIFIER = ns("treeselect")
    const WIDGET_WRAPPER_CLASS = `.${WIDGET_IDENTIFIER}__wrapper`
    const WIDGET_WRAPPER = `.${WIDGET_IDENTIFIER} > ${WIDGET_WRAPPER_CLASS}`
    const WIDGET_DISCLOSURE_BTN = `.${WIDGET_IDENTIFIER}__button`
    const MAIN_DROPDOWN = `.${WIDGET_IDENTIFIER}__collapse`
    const WIDGET_COLLAPSE_BUTTON = `${WIDGET_WRAPPER} > ${WIDGET_DISCLOSURE_BTN}`
    const WIDGET_COLLAPSE = `${WIDGET_WRAPPER} > ${WIDGET_DISCLOSURE_BTN} + ${MAIN_DROPDOWN}`
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

    class TreeselectButton extends Instance {
        static get instanceClassName() {
            return "TreeselectButton"
        }
    }

    class TreeselectGroup extends Instance {
        static get instanceClassName() {
            return "TreeselectGroup"
        }

        init() {
            this._items = new Map()
            this.initSelectableGroup()
        }

        initSelectableGroup() {
            /** @type {HTMLElement} */
            const label = this.element.node.querySelector("& > .fr-treeselect__group-header .fr-label[aria-controls]")
            /** @type {HTMLElement} */
            const collapse = this.element.node.querySelector(`& > .fr-collapse`)
            if (label === null || collapse === null) return

            const ariaControls = label.getAttribute("aria-controls")
            const labelText = label.textContent.trim()

            collapse.classList.remove("fr-collapse")
            collapse.id = ariaControls
            label.textContent = ""
            label.removeAttribute("aria-controls")
            label.parentElement.classList.add("fr-treeselect__group-selectable")
            label.parentElement.querySelector("input").setAttribute("aria-label", labelText)
            label.parentElement.insertAdjacentHTML(
                "beforeend",
                this.selectableGroupsAccordionButton(ariaControls, labelText),
            )
            requestAnimationFrame(() => collapse.classList.add("fr-collapse"))
        }

        selectableGroupsAccordionButton(ariaControls, textContent) {
            return `<button type="button" class="fr-treeselect__group-button fr-accordion__btn" aria-expanded="false" aria-controls="${ariaControls}">${textContent}</button>`
        }
    }

    class Treeselect extends Instance {
        static SEARCH = ns.event("search")

        static get instanceClassName() {
            return "Treeselect"
        }

        get button() {
            try {
                return this.getRegisteredInstances(TreeselectButton.instanceClassName)[0]
            } catch (_) {
                this.error(
                    "Unable to locate the treeselect buttton; you're probably missing a "
                        + `button${WIDGET_DISCLOSURE_BTN} inside ${WIDGET_WRAPPER_CLASS}`,
                )
                return null
            }
        }

        init() {
            this.register(WIDGET_COLLAPSE_BUTTON, TreeselectButton)
            this.register(`${MAIN_DROPDOWN} > .${WIDGET_IDENTIFIER}__head > .fr-search-bar`, SearchBar)
            this.register(WIDGET_GROUP, TreeselectGroup)

            this.addAscent(SearchBar.SEARCH, this.onSearch.bind(this))
            this.descend(SearchBar.RETRIEVE)

            this.listen(DisclosureEvent.DISCLOSE, this.onOpen.bind(this))

            this.initDisclosureButton()
        }

        initDisclosureButton() {
            const collapse = this.element.node.querySelector(WIDGET_COLLAPSE)
            if (!collapse) return

            if (collapse.id === "") {
                collapse.id = uniqueId("fr-treeselect-subgroup")
            }
            const button = collapse.parentElement.querySelector(WIDGET_DISCLOSURE_BTN)

            collapse.classList.remove("fr-collapse")
            button.setAttribute("type", "button")
            button.setAttribute("aria-controls", collapse.id)
            button.setAttribute("aria-expanded", "false")
            requestAnimationFrame(() => collapse.classList.add("fr-collapse"))
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
