import {applicationReady} from "Application"
import {Controller} from "Stimulus"
import {debounce, search} from "Utils"

/**
 * *** Targets ***
 * @property {HTMLInputElement} inputTarget
 * *** Values ***
 * @property {Boolean} hiddenValue
 * @property {Number} minSearchLengthValue
 */
class TreeselectElement extends Controller {
    static values = {hidden: {type: Boolean, default: false}, minSearchLength: {type: Number, default: 3}}
    static targets = ["input"]

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

    hiddenValueChanged(hidden, previous) {
        if (hidden) {
            this.element.setAttribute("hidden", "hidden")
        } else {
            this.element.removeAttribute("hidden")
        }
        if (previous !== undefined && hidden !== previous) {
            this.dispatch("visibility", {detail: {hidden}, prefix: "treeselect"})
        }
    }

    async search(value) {
        if (value.length < this.minSearchLengthValue) {
            this.hiddenValue = false
            return
        }

        for (const label of this.labels) {
            if (search(label, value)) {
                this.hiddenValue = false
                return
            }
        }
        this.hiddenValue = true
    }
}

/**
 * *** Targets ***
 * @property {HTMLElement[]} collapseTargets
 * @property {HTMLInputElement[]} inputTargets
 * *** Values ***
 * @property {Boolean} hiddenValue
 * @property {Boolean} childrenFilteredValue
 * @property {Boolean} selfFilteredValue
 * *** Outlets ***
 * @property {TreeselectElement[]} treeselectElementOutlets
 */
class TreeselectGroup extends Controller {
    static values = {selfFiltered: Boolean, childrenFiltered: Boolean}
    static targets = ["input", "collapse"]
    static outlets = ["treeselect-element"]

    get labels() {
        return this.inputTargets.flatMap(it => [
            ...Array.from(it.labels).map(it => it.textContent.trim()),
            it.ariaLabel?.trim() ?? "",
        ])
    }

    initialize() {
        for (const it of this.element.querySelectorAll("& > .fr-treeselect__group-header input")) {
            it.setAttribute(`data-${this.identifier}-target`, "input")
        }
        this.refresh = debounce(this.refresh.bind(this), 150, {leading: true})
    }

    async search(value) {
        if (value.length < 3) {
            this.selfFilteredValue = false
            return
        }

        for (const label of this.labels) {
            if (search(label, value)) {
                this.selfFilteredValue = false
                return
            }
        }

        this.selfFilteredValue = true
    }

    elementFiltered({detail: {hidden}}) {
        if (!hidden) {
            this.childrenFilteredValue = false
            return
        }

        for (const outlet of this.treeselectElementOutlets) {
            if (!outlet.hiddenValue) {
                this.childrenFilteredValue = false
                return
            }
        }
        this.childrenFilteredValue = true
    }

    selfFilteredValueChanged(hidden, previous) {
        if (previous === undefined || hidden === previous) return
        this.refresh()
    }

    childrenFilteredValueChanged(hidden, previous) {
        if (previous === undefined || hidden === previous) return
        this.refresh()
    }

    refresh() {
        requestAnimationFrame(() => {
            const hidden = this.childrenFilteredValue && this.selfFilteredValue
            if (hidden) {
                this.element.setAttribute("hidden", "hidden")
            } else {
                this.element.removeAttribute("hidden")
                if (!this.childrenFilteredValue) {
                    this.collapseTargets.forEach(it => dsfr(it).collapse.disclose())
                } else {
                    this.collapseTargets.forEach(it => dsfr(it).collapse.conceal())
                }
            }
            this.dispatch("visibility", {detail: {hidden}, prefix: "treeselect"})
        })
    }
}

/**
 * *** Targets ***
 * @property {HTMLElement} bodyTarget
 * @property {HTMLButtonElement} buttonTarget
 * *** Outlets ***
 * @property {TreeselectElement[]} treeselectElementOutlets
 * @property {TreeselectGroup[]} treeselectGroupOutlets
 */
class Treeselect extends Controller {
    static targets = ["body", "button"]
    static outlets = ["treeselect-element", "treeselect-group"]

    initialize() {
        this.choices = new Map()
        this.filter = debounce(
            search => {
                for (const it of this.treeselectElementOutlets) {
                    it.search(search)
                }
                for (const it of this.treeselectGroupOutlets) {
                    it.search(search)
                }
            },
            300,
            {leading: true},
        )
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

    onSearch({detail: {search}}) {
        this.filter(search.trim())
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
    app.register("treeselect-element", TreeselectElement)
    app.register("treeselect-group", TreeselectGroup)
    app.register("treeselect", Treeselect)
})
