import {applicationReady, dsfrDisclosePromise} from "Application"
import {Controller} from "Stimulus"
import {search} from "Utils"

const WIDGET_IDENTIFIER = "treeselect"
const GROUP_IDENTIFIER = "treeselect-group"
const MIN_SEARCH_LEN = 3

let counter = 0

class TreeselectGroupConnectable extends Controller {
    connect() {
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
    }
}

/**
 * *** Targets ***
 * @property {HTMLInputElement} inputTarget
 * *** Values ***
 * @property {Boolean} hiddenValue
 */
class TreeselectElement extends TreeselectGroupConnectable {
    static values = {hidden: {type: Boolean, default: false}}
    static targets = ["input"]

    get labels() {
        return [
            ...Array.from(this.inputTarget.labels).map(it => it.textContent.trim()),
            this.inputTarget.ariaLabel?.trim() ?? "",
        ]
    }

    get isHidden() {
        return this.hiddenValue
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

    async search(value) {
        if (value.length < MIN_SEARCH_LEN) {
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
 * @property {HTMLInputElement[]} inputTargets
 * @property {HTMLInputElement[]} accordionBtnTargets
 * *** Values ***
 * @property {Boolean} hiddenValue
 * @property {Boolean} hasChildrenMatchingValue
 * @property {Boolean} selfMatchesSearchValue
 */
class TreeselectGroup extends TreeselectGroupConnectable {
    static values = {
        hidden: {type: Boolean, default: false},
        selfMatchesSearch: {type: Boolean, default: true},
        hasChildrenMatching: {type: Boolean, default: true},
    }
    static targets = ["input", "accordionBtn", "collapse"]

    get labels() {
        const result = []
        for (const it of this.inputTargets) {
            result.push(...Array.from(it.labels).map(it => it.textContent.trim()))
            result.push(it.ariaLabel?.trim() ?? "")
        }
        return result
    }

    initialize() {
        this.children = new Map()

        for (const it of this.element.querySelectorAll("& > .fr-treeselect__group-header input")) {
            it.setAttribute(`data-${this.identifier}-target`, "input")
        }
    }

    registerChild(id, child) {
        this.children.set(id, child)
    }

    unregisterChild(id) {
        this.children.delete(id)
    }

    async search(value) {
        // We need to trigger search on the children anyway to always ensure proper visibility
        const results = await Promise.all(this.children.values().map(it => it.search(value)))

        // If search is less than MIN_SEARCH_LEN, resets the group: everything is visible, accordions are collapsed
        if (value.length < MIN_SEARCH_LEN) {
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
}

/**
 * *** Values ***
 * @property {Number} minSearchLengthValue
 * *** Targets ***
 * @property {HTMLElement} bodyTarget
 * @property {HTMLButtonElement} buttonTarget
 */
class Treeselect extends Controller {
    static targets = ["body", "button"]
    static values = {minSearchLength: {type: Number, default: 3}}

    initialize() {
        this.choices = new Map()
        this.children = new Map()
    }

    bodyTargetConnected(el) {
        for (const /**@type {HTMLInputElement} */ it of el.querySelectorAll("input")) {
            const actions = [`change->${this.identifier}#onChange`, it.dataset.action || ""]
            it.dataset.action = actions.join(" ").trim()
            requestAnimationFrame(() => it.dispatchEvent(new Event("change")))
        }
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
        await Promise.all(this.children.values().map(it => it.search(search)))
    }

    onChange({target}) {
        const label = target.labels[0].textContent.trim() || target.ariaLabel
        if (target.checked) {
            this.choices.set(target.value, label)
        } else {
            this.choices.delete(target.value)
        }
        const size = this.choices.size
        if (size === 0) {
            this.buttonTarget.textContent = this.originalButtonLabel
        } else if (size === 1) {
            this.buttonTarget.textContent = `${this.choices.values().next().value}`
        } else {
            const additionnal = this.choices.size - 1
            this.buttonTarget.textContent = `${this.choices.values().next().value} +${additionnal} élément${additionnal > 1 ? "s" : ""}`
        }
    }
}

applicationReady.then(app => {
    app.register(WIDGET_IDENTIFIER, Treeselect)
    app.register(GROUP_IDENTIFIER, TreeselectGroup)
    app.register("treeselect-element", TreeselectElement)
})
