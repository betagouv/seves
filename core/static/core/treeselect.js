const dsfrInitialized = new Promise((resolve, reject) => {
    function test () {
        return typeof window.dsfr === "function"
    }

    if (test()) {
        resolve(window.dsfr)
    } else {
        const interval = 100  // milliseconds
        const timeout = 5000 / interval  // milliseconds
        let retryCount = 0
        const id = setInterval(() => {
            if (test()) {
                clearInterval(id)
                return resolve(window.dsfr)
            }

            if (retryCount > timeout) {
                clearInterval(id)
                return reject("dsfr not initialized after 5s")
            }

            retryCount++
        }, interval)
    }
})

function debounce (fn, delay = 300) {
    let timerId
    return function (...args) {
        clearTimeout(timerId)
        timerId = setTimeout(() => {
            timerId = null
            fn.apply(this, args)
        }, delay)
        fn.apply(this, args)
    }
}

dsfrInitialized.then((dsfr) => {
    // Import for the poor
    const {core: {Instance}, checkbox: {CheckboxEmission}, internals: {register, ns: {emission}}} = dsfr

    const WIDGET_IDENTIFIER = "fr-treeselect"
    const WIDGET_WRAPPER_CLASS = `.${WIDGET_IDENTIFIER}__wrapper`
    const WIDGET_WRAPPER = `.${WIDGET_IDENTIFIER} > ${WIDGET_WRAPPER_CLASS}`
    const WIDGET_DISCLOSURE_BTN = `.${WIDGET_IDENTIFIER}__button`
    const MAIN_DROPDOWN = `.${WIDGET_IDENTIFIER}__collapse`
    const WIDGET_COLLAPSE_BUTTON = `${WIDGET_WRAPPER} > ${WIDGET_DISCLOSURE_BTN}`
    const WIDGET_COLLAPSE = `${WIDGET_WRAPPER} > ${WIDGET_DISCLOSURE_BTN} + ${MAIN_DROPDOWN}`
    const WIDGET_CONTENT = `${WIDGET_WRAPPER} .${WIDGET_IDENTIFIER}__body`
    const WIDGET_SELECTABLE_GROUP = `${WIDGET_CONTENT} .${WIDGET_IDENTIFIER}__group-header > .fr-checkbox-group > [aria-controls]`
    const WIDGET_NORMAL_GROUP = `${WIDGET_CONTENT} .${WIDGET_IDENTIFIER}__group-header > .fr-treeselect__group-button[aria-controls]`

    class SearchBar extends Instance {
        static CHANGE = emission('treeselect-searchbar', 'change')
        static RETRIEVE = emission('treeselect-searchbar', 'retrieve')

        static get instanceClassName () {return "TreeselectSearchbar"}

        init () {
            this.__onChange = this.onChange.bind(this)
            const debouncedOnChange = debounce(this.__onChange)
            /**
             * @type {Object<string, Object<string, EventListenerOrEventListenerObject>>}
             * @private
             */
            this._boundListeners = {
                '.fr-input[type="search"]': {
                    "focus": debouncedOnChange,
                    "input": debouncedOnChange
                },
            }

            this._boundListenersForEach((el, type, listener) => el.addEventListener(type, listener))
            this.addDescent(this.constructor.RETRIEVE, this.__onChange)
        }

        onChange (evt) {
            this.ascend(SearchBar.CHANGE, evt.target.value);
        }

        dispose () {
            this._boundListenersForEach((el, type, listener) => el.removeEventListener(type, listener))
        }

        /**
         * @param {function(el: Element, type: string, listener: EventListenerOrEventListenerObject)} callback
         * @private
         */
        _boundListenersForEach (callback) {
            Object.entries(this._boundListeners).forEach(([selector, events]) => {
                this.node.querySelectorAll(selector).forEach(el => {
                    Object.entries(events).forEach(([type, listener]) => {
                        callback(el, type, listener);
                    })
                })
            })
        }
    }

    class TreeselectButton extends Instance {
        static get instanceClassName () {return "TreeselectButton"}

        get originalLabelAttributeName () {return `${this.registration.attribute}-label`}

        get label () {return this.node.textContent.trim()}

        set label (value) {
            if (!value) {
                this.node.textContent = this.getAttribute(this.originalLabelAttributeName)
            } else {
                this.node.textContent = value
            }
        }

        init () {
            this.setAttribute(this.originalLabelAttributeName, this.label)
        }
    }

    class Treeselect extends Instance {
        static get instanceClassName () {return "Treeselect"}

        get button () {
            try {
                return this.getRegisteredInstances("TreeselectButton")[0]
            } catch (_) {
                this.error(
                    "Unable to locate the treeselect buttton; you're probably missing a "
                    + `button${WIDGET_DISCLOSURE_BTN} inside ${WIDGET_WRAPPER_CLASS}`
                )
            }
        }

        init () {
            this.choices = new Map()

            this.register(WIDGET_COLLAPSE_BUTTON, TreeselectButton)
            this.register(`${MAIN_DROPDOWN} > .${WIDGET_IDENTIFIER}__head > .fr-search-bar`, SearchBar)

            this.initSelectableGroups()
            this.initNormalGroups()
            this.initDisclosureButton()

            // Handle checkboxes
            if (dsfr.checkbox) {
                this.addAscent(CheckboxEmission.CHANGE, this.onCheckboxChange.bind(this));
                this.descend(CheckboxEmission.RETRIEVE);
            }

            // Handle searchbar
            this.addAscent(SearchBar.CHANGE, this.onSearch.bind(this));
            this.descend(SearchBar.RETRIEVE);
        }

        initSelectableGroups () {
            this.element.node.querySelectorAll(WIDGET_SELECTABLE_GROUP).forEach(button => {
                const container = button.parentElement
                const ariaControls = button.getAttribute("aria-controls")
                const label = button.textContent.trim()

                button.removeAttribute("aria-controls")
                button.removeAttribute("aria-expanded")
                button.textContent = ""

                container.querySelector("input").setAttribute("aria-label", label)
                container.classList.add("fr-accordion")
                container.insertAdjacentHTML("beforeend", this.selectableGroupsAccordionButton(ariaControls, label))
            })
        }

        initNormalGroups () {
            this.element.node.querySelectorAll(WIDGET_NORMAL_GROUP).forEach(button => {
                const container = button.parentElement
                container.classList.add("fr-accordion")
                button.classList.add("fr-accordion__btn")
                button.setAttribute("type", "button")
            })
        }

        initDisclosureButton () {
            const dropdown = this.element.node.querySelector(WIDGET_COLLAPSE)
            if (!dropdown) return;
            if (!dropdown.id) {
                const randomString = Math.floor(Math.random() * 2e16).toString(16)
                dropdown.id = `${WIDGET_IDENTIFIER}-${randomString}`
            }
            const button = dropdown.parentElement.querySelector(WIDGET_DISCLOSURE_BTN)
            button.setAttribute("type", "button")
            button.setAttribute("aria-controls", dropdown.id)
            button.setAttribute("aria-expanded", "false")
            dropdown.classList.add("fr-collapse")
        }

        selectableGroupsAccordionButton (ariaControls, textContent) {
            return `<button type="button" class="fr-accordion__btn" aria-expanded="false" aria-controls="${ariaControls}">${textContent}</button>`
        }

        onCheckboxChange (node) {
            const label = node.labels[0].textContent.trim() || node.ariaLabel
            if (node.checked) {
                debugger
                this.choices.set(node.name, label)
            } else {
                this.choices.delete(node.name)
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

        onSearch (value) {
        }
    }

    register(`.${WIDGET_IDENTIFIER}`, Treeselect)
})

export {dsfrInitialized}
