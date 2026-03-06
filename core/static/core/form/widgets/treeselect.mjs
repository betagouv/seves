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
        reject("dsfr not initialized after 5s")
    }, 5000)
    window.addEventListener("dsfr.start", dsfrStart)
})

dsfrInitialized.then(dsfr => {
    // Imports (kind of)
    const {
        core: {Instance},
        checkbox: {CheckboxEmission},
        internals: {
            register,
            ns,
            dom: {uniqueId},
        },
    } = dsfr

    const collator = new Intl.Collator(navigator.language, {
        usage: "search",
        sensitivity: "base",
    })

    // Inspired by https://github.com/idmadj/locale-includes/blob/master/src/index.js
    function localeIncludes(haystack, needle) {
        const haystackLength = haystack.length
        const needleLength = needle.length
        const lengthDiff = haystackLength - needleLength

        for (let i = 0; i++ <= lengthDiff; ) {
            const subHaystack = haystack.substring(i, i + needleLength)
            if (collator.compare(subHaystack, needle) === 0) {
                return true
            }
        }
        return false
    }

    const WIDGET_IDENTIFIER = ns("treeselect")
    const WIDGET_WRAPPER_CLASS = `.${WIDGET_IDENTIFIER}__wrapper`
    const WIDGET_WRAPPER = `.${WIDGET_IDENTIFIER} > ${WIDGET_WRAPPER_CLASS}`
    const WIDGET_DISCLOSURE_BTN = `.${WIDGET_IDENTIFIER}__button`
    const MAIN_DROPDOWN = `.${WIDGET_IDENTIFIER}__collapse`
    const WIDGET_COLLAPSE_BUTTON = `${WIDGET_WRAPPER} > ${WIDGET_DISCLOSURE_BTN}`
    const WIDGET_COLLAPSE = `${WIDGET_WRAPPER} > ${WIDGET_DISCLOSURE_BTN} + ${MAIN_DROPDOWN}`
    const WIDGET_GROUP = `${WIDGET_WRAPPER} .${WIDGET_IDENTIFIER}__group`

    /**
     * @property {HTMLInputElement} node
     */
    class TreeselectInputGroup extends Instance {
        static SELECTOR = ns.selector("treeselect-input-group")
        static CHANGE = ns.emission("treeselect-input", "change")
        static RETRIEVE = ns.emission("treeselect-input", "retrieve")

        static get instanceClassName() {
            return "TreeselectInputGroup"
        }

        get isFiltered() {
            return this._isFiltered
        }

        get checkboxes() {
            return Array.from(this.node.querySelectorAll("input"))
        }

        get labels() {
            return this.checkboxes.flatMap(it => Array.from(it.labels))
        }

        init() {
            this._isFiltered = false
            this.addDescent(Treeselect.SEARCH, this.onSearch.bind(this))
            this.addDescent(this.constructor.RETRIEVE, this.triggerChange.bind(this))
        }

        triggerChange() {
            this.ascend(this.constructor.CHANGE, this)
        }

        setFiltered(value) {
            if (value !== this._isFiltered) {
                this._isFiltered = value
                this.triggerChange()
            }
        }

        onSearch(value) {
            if (value === "" || this.labels.some(label => localeIncludes(label.textContent, value))) {
                this.node.removeAttribute("hidden")
                this.setFiltered(false)
            } else {
                this.node.setAttribute("hidden", "hidden")
                this.setFiltered(true)
            }
        }
    }

    class SearchBar extends Instance {
        static SEARCH = ns.emission("treeselect-search", "change")
        static RETRIEVE = ns.emission("treeselect-search", "retrive")

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
        }

        onChange(evt) {
            this.ascend(this.constructor.SEARCH, evt.target.value)
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

        get originalLabelAttributeName() {
            return `${this.registration.attribute}-label`
        }

        get label() {
            return this.node.textContent.trim()
        }

        set label(value) {
            if (!value) {
                this.node.textContent = this.getAttribute(this.originalLabelAttributeName)
            } else {
                this.node.textContent = value
            }
        }

        init() {
            this.setAttribute(this.originalLabelAttributeName, this.label)
        }
    }

    class TreeselectGroup extends Instance {
        static get instanceClassName() {
            return "TreeselectGroup"
        }

        init() {
            this._items = new Map()
            this.initSelectableGroup()
            this.addDescent(Treeselect.SEARCH, this.onSearch.bind(this))
            this.addAscent(TreeselectInputGroup.CHANGE, this.onChildrenFiltered.bind(this))
            this.descend(TreeselectInputGroup.RETRIEVE)
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

        onSearch(_value) {}

        onChildrenFiltered(node) {
            if (!this._items.has(node.element.id)) {
                this._items.set(node.element.id, new WeakRef(node))
            }
            if (!node.isFiltered) {
                return this.node.removeAttribute("hidden")
            }
            for (const ref of this._items.values()) {
                const item = ref.deref()
                if (item !== undefined && !item.isFiltered) {
                    return this.node.removeAttribute("hidden")
                }
            }
            this.node.setAttribute("hidden", "hidden")
        }
    }

    class Treeselect extends Instance {
        static SEARCH = ns.emission("treeselect", "search")

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

        get searchBar() {
            const instances = this.getRegisteredInstances(SearchBar.instanceClassName)
            return instances.length > 0 ? instances[0] : null
        }

        init() {
            this.choices = new Map()
            this.register(WIDGET_COLLAPSE_BUTTON, TreeselectButton)
            this.register(`${MAIN_DROPDOWN} > .${WIDGET_IDENTIFIER}__head > .fr-search-bar`, SearchBar)
            this.register(`${MAIN_DROPDOWN} ${TreeselectInputGroup.SELECTOR}`, TreeselectInputGroup)
            this.register(WIDGET_GROUP, TreeselectGroup)

            this.addAscent(SearchBar.SEARCH, this.onSearch.bind(this))
            this.descend(SearchBar.RETRIEVE)

            this.addAscent(CheckboxEmission.CHANGE, this.onCheckboxChange.bind(this))
            this.descend(CheckboxEmission.RETRIEVE)

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

        /** @param {HTMLInputElement} node */
        onCheckboxChange(node) {
            const label = node.labels[0].textContent.trim() || node.ariaLabel
            if (node.checked) {
                this.choices.set(node.value, label)
            } else {
                this.choices.delete(node.value)
            }

            const size = this.choices.size
            if (size === 0) {
                this.button.label = ""
            } else if (size === 1) {
                this.button.label = `${this.choices.values().next().value}`
            } else {
                this.button.label = `${this.choices.values().next().value} +${this.choices.size - 1}`
            }
        }

        onSearch(value) {
            this.descend(this.constructor.SEARCH, value)
        }
    }

    register(`.${WIDGET_IDENTIFIER}`, Treeselect)
}, console.error)

export {dsfrInitialized}
