import {applicationReady, dsfrDisclosePromise} from "Application"
import {Controller} from "Stimulus"
import {search} from "Utils"

const WIDGET_IDENTIFIER = "treeselect"
const GROUP_IDENTIFIER = "treeselect-group"
const CHOICES_CHANGED_EVENT = "choices"

let counter = 0

class TreeselectChoicesListener extends Controller {
    connect() {
        /** @type {Treeselect} */
        this.treeselect = this.application.getControllerForElementAndIdentifier(
            this.element.closest(`[data-controller~="${WIDGET_IDENTIFIER}"]`),
            WIDGET_IDENTIFIER,
        )
        this.onChoicesChanged = this.onChoicesChanged.bind(this)
        this.treeselect.element.addEventListener(`${WIDGET_IDENTIFIER}:${CHOICES_CHANGED_EVENT}`, this.onChoicesChanged)
    }

    disconnect() {
        this.treeselect.element.removeEventListener(
            `${WIDGET_IDENTIFIER}:${CHOICES_CHANGED_EVENT}`,
            this.onChoicesChanged,
        )
    }
}

/**
 * *** Targets ***
 * @property {HTMLInputElement[]} inputTargets
 * @property {HTMLInputElement} inputTarget
 * @property {boolean} hasInputTarget
 */
class TreeselectGroupConnectable extends TreeselectChoicesListener {
    static targets = ["input"]

    connect() {
        super.connect()

        const enclosingGroup = this.element.parentElement.closest(
            `[data-controller~="${WIDGET_IDENTIFIER}"], [data-controller~="${GROUP_IDENTIFIER}"]`,
        )
        if (enclosingGroup != null) {
            this._childId = `${counter++}`
            /** @type {TreeselectGroup | null} */
            this._parentGroup =
                this.application.getControllerForElementAndIdentifier(enclosingGroup, WIDGET_IDENTIFIER)
                ?? this.application.getControllerForElementAndIdentifier(enclosingGroup, GROUP_IDENTIFIER)
            this._parentGroup?.registerChild(this._childId, this)
        }
    }

    disconnect() {
        this._parentGroup?.unregisterChild(this._childId, this)
        super.disconnect()
    }

    /**
     * @param {CustomEvent} param0
     * @param {Object} param0.detail
     * @param {Map<string, string>} param0.detail.choices
     */
    async onChoicesChanged({target, detail: {choices}}) {
        for (const it of this.inputTargets) {
            if (target === it) continue
            if (choices.has(it.value.trim()) && !it.checked) {
                it.checked = true
            } else if (!choices.has(it.value.trim()) && it.checked) {
                it.checked = false
            }
        }
    }
}

/**
 * *** Values ***
 * @property {Boolean} hiddenValue
 */
class TreeselectElement extends TreeselectGroupConnectable {
    static values = {hidden: {type: Boolean, default: false}}

    get labels() {
        return [
            ...Array.from(this.inputTarget.labels).map(it => it.textContent.trim()),
            this.inputTarget.ariaLabel?.trim() ?? "",
        ]
    }

    initialize() {
        for (const it of this.element.querySelectorAll("input")) {
            it.setAttribute(`data-${this.identifier}-target`, "input")
        }
    }

    hiddenValueChanged(hidden) {
        if (hidden) {
            this.element.setAttribute("hidden", "hidden")
        } else {
            this.element.removeAttribute("hidden")
        }
    }

    async search(value, minlength) {
        if (value.length < minlength) {
            this.hiddenValue = false
            return true
        }
        for (const label of this.labels) {
            if (search(label, value)) {
                this.hiddenValue = false
                return true
            }
        }
        this.hiddenValue = true
        return false
    }
}

/**
 * *** Targets ***
 * @property {HTMLElement[]} collapseTargets
 * @property {HTMLInputElement[]} accordionBtnTargets
 * *** Values ***
 * @property {Boolean} hiddenValue
 * @property {Boolean} autoSelectChildrenValue
 */
class TreeselectGroup extends TreeselectGroupConnectable {
    static values = {
        hidden: {type: Boolean, default: false},
        autoSelectChildren: {type: Boolean, default: false},
    }
    static targets = ["accordionBtn", "collapse"]

    #locked = false

    get canAutoSelectChildren() {
        return this.inputTarget.type === "checkbox" && this.autoSelectChildrenValue
    }

    get labels() {
        const result = []
        for (const it of this.inputTargets) {
            result.push(...Array.from(it.labels).map(it => it.textContent.trim()))
            result.push(it.ariaLabel?.trim() ?? "")
        }
        return result
    }

    get childTargets() {
        return Array.from(this.children.values()).flatMap(child => child.inputTargets)
    }

    initialize() {
        /** @type {Map<string, TreeselectGroupConnectable>} */
        this.children = new Map()
    }

    registerChild(id, child) {
        this.children.set(id, child)
    }

    unregisterChild(id) {
        this.children.delete(id)
    }

    async search(value, minlength) {
        // We need to trigger search on the children anyway to always ensure proper visibility
        const results = await Promise.all(this.children.values().map(it => it.search(value, minlength)))

        // If search is less than MIN_SEARCH_LEN, resets the group: everything is visible, accordions are collapsed
        if (value.length < minlength) {
            this.hiddenValue = false
            this.collapseTargets.forEach(it => dsfr(it).collapse.conceal())
            return true
        }

        // If there are results within children, open accordion
        if (results.some(it => it)) {
            this.hiddenValue = false
            this.collapseTargets.forEach(it => dsfrDisclosePromise(dsfr(it).collapse))
            return true
        }

        // Finally, search self
        for (const label of this.labels) {
            if (search(label, value)) {
                this.hiddenValue = false
                return true
            }
        }

        this.hiddenValue = true
        return false
    }

    hiddenValueChanged(hidden) {
        if (hidden) {
            this.element.setAttribute("hidden", "hidden")
        } else {
            this.element.removeAttribute("hidden")
        }
    }

    async onChoicesChanged(evt) {
        if (this.#locked) return

        await super.onChoicesChanged(evt)
        if (!this.hasInputTarget || !this.canAutoSelectChildren) return

        try {
            this.#locked = true
            const hasAll = this.childTargets.every(it => it.checked)
            if (hasAll && !this.inputTarget.checked) {
                this.inputTarget.checked = true
                this.inputTarget.dispatchEvent(new Event("change"))
            } else if (!hasAll && this.inputTarget.checked) {
                this.inputTarget.checked = false
                this.inputTarget.dispatchEvent(new Event("change"))
            }
        } finally {
            this.#locked = false
        }
    }

    /** @param {Event} evt */
    onSelect(evt) {
        if (this.#locked || !this.hasInputTarget) return

        const checked = evt.target.checked
        if (this.canAutoSelectChildren) {
            try {
                this.#locked = true
                for (const it of this.childTargets) {
                    it.checked = checked
                    it.dispatchEvent(new Event("change"))
                }
            } finally {
                this.#locked = false
            }
        }

        // Open group accordion
        if (checked) {
            this.collapseTargets.forEach(async it => {
                await dsfrDisclosePromise(dsfr(it).collapse)
                it.scrollIntoView({block: "center"})
            })
        }
    }
}

/**
 * *** Values ***
 * @property {String} formvalValue
 */
class TreeselectSelectedBadge extends TreeselectChoicesListener {
    static values = {formval: String}

    /**
     * @param {CustomEvent} param0
     * @param {Object} param0.detail
     * @param {Map<string, string>} param0.detail.choices
     */
    onChoicesChanged({detail: {choices}}) {
        if (!choices.has(this.formvalValue)) {
            this.element.remove()
        }
    }

    onDeleteClick() {
        const inputs = this.treeselect.element.querySelectorAll(`input[value="${this.formvalValue}"]`)
        for (const it of inputs) {
            it.checked = false
            it.dispatchEvent(new Event("change"))
        }
    }
}

/**
 * *** Values ***
 * @property {Number} minSearchLengthValue
 * *** Targets ***
 * @property {HTMLElement} bodyTarget
 * @property {HTMLButtonElement} buttonTarget
 * @property {HTMLInputElement} searchbarTarget
 * @property {HTMLButtonElement[]} unselectAllBtnTargets
 * @property {HTMLElement} selectedGroupTarget
 * @property {HTMLButtonElement} selectedTagTarget
 * @property {HTMLButtonElement[]} selectedTagTargets
 * @property {HTMLTemplateElement} selectedTagTplTarget
 */
class Treeselect extends Controller {
    static targets = ["body", "button", "searchbar", "unselectAllBtn", "selectedGroup", "selectedTag", "selectedTagTpl"]
    static values = {minSearchLength: {type: Number, default: 3}}

    initialize() {
        this.choices = new Map()
        this.children = new Map()
        this.element.dataset.action = [
            `${this.identifier}:${CHOICES_CHANGED_EVENT}->${this.identifier}#onChoicesChange`,
            ...(this.element.dataset.action ?? "").split(/\s+/g),
        ].join(" ")
    }

    connect() {
        new Promise(resolve => {
            for (const it of this.element.querySelectorAll("input:checked")) {
                this.onChange({target: it})
            }
            resolve()
        })
    }

    buttonTargetConnected(el) {
        this.originalButtonLabel = el.textContent.trim()
    }

    registerChild(id, child) {
        this.children.set(id, child)
    }

    unregisterChild(id) {
        this.children.delete(id)
    }

    async onSearch({detail: {search}}) {
        await Promise.all(this.children.values().map(it => it.search(search, this.minSearchLengthValue)))
    }

    /**
     * @param {Event} param0
     * @param {HTMLInputElement} param0.target
     */
    onChange({target}) {
        const label = target.labels[0].textContent.trim() || target.ariaLabel
        const value = target.value.trim()
        const categorisedLabel = target.dataset.categorisedLabel || label

        // Don't process event if already in corect state
        if (this.choices.has(value) === target.checked) return

        // If inputs are radio buttons, we allow only one value
        if (target.type === "radio") {
            this.choices.clear()
        }

        if (target.checked) {
            this.choices.set(value, categorisedLabel)
            this.selectedGroupTarget.insertAdjacentHTML(
                "beforeend",
                this.selectedTagTplTarget.innerHTML.replaceAll("__label__", label).replaceAll("__value__", value),
            )
        } else {
            this.choices.delete(value)
        }
        this.dispatch(CHOICES_CHANGED_EVENT, {target, detail: {choices: this.choices}})
    }

    onUnselectAll() {
        for (const it of this.element.querySelectorAll("input:checked")) {
            it.checked = false
        }
        this.choices.clear()
        this.dispatch(CHOICES_CHANGED_EVENT, {detail: {choices: this.choices}})
    }

    onChoicesChange() {
        const size = this.choices.size
        if (size === 0) {
            this.buttonTarget.textContent = this.originalButtonLabel
        } else if (size === 1) {
            this.buttonTarget.textContent = `${this.choices.values().next().value}`
        } else {
            this.buttonTarget.textContent = `${this.choices.size} éléments`
        }
        this.unselectAllBtnTargets.forEach(it => it.classList.toggle("fr-hidden", size === 0))
    }

    onEraseSearch() {
        this.searchbarTarget.value = ""
        this.searchbarTarget.dispatchEvent(new Event("input"))
    }
}

applicationReady.then(app => {
    app.register(WIDGET_IDENTIFIER, Treeselect)
    app.register(GROUP_IDENTIFIER, TreeselectGroup)
    app.register("treeselect-selected-badge", TreeselectSelectedBadge)
    app.register("treeselect-element", TreeselectElement)
})
