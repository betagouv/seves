import {applicationReady, escapeHTML} from "Application"
import {Controller} from "Stimulus"
import {VirtualOptionList} from "VirtualOptionList"

const FREQUENT_GROUP_LABEL = "Les plus fréquentes"
const OTHER_GROUP_LABEL = "Autres"
const ESPECE_WIDGET_ID = "fr-treeselect-id_pre_creation_espece"
const OPTION_TEMPLATE_ID = "espece-option-template"
const VIRTUALIZE_THRESHOLD = 200

let uid = 0

class EspeceGrouping extends Controller {
    static targets = ["maladieInput"]

    #byMaladie = {}
    #allSpecies = []
    #virtualOther = null

    initialize() {
        this.#byMaladie = JSON.parse(this.element.querySelector("#espece-options-by-maladie")?.innerText ?? "{}")
        this.#allSpecies = JSON.parse(this.element.querySelector("#all-especes")?.innerText ?? "[]")
    }

    connect() {
        this.#setDisabled(true)
    }

    get especeWidget() {
        return document.getElementById(ESPECE_WIDGET_ID)
    }

    maladieInputTargetConnected(el) {
        if (el.type === "radio" && el.checked) {
            el.dispatchEvent(new Event("change"))
        }
    }

    onMaladieSelected({target}) {
        if (!target.checked) {
            this.#clear()
            return
        }
        const entry = this.#byMaladie[target.value]
        if (!entry) {
            this.#clear()
            return
        }
        const frequentIds = new Set(entry.frequent.map(it => String(it.id)))
        const other = this.#allSpecies.filter(it => !frequentIds.has(String(it.id)))
        this.#populate({frequent: entry.frequent, other})
        this.#setDisabled(false)
    }

    #clear() {
        this.#getTreeselectController()?.unselectAll()
        const groups = this.#groupContainers()
        if (groups) {
            groups.frequent.replaceChildren()
            if (this.#virtualOther) {
                this.#virtualOther.clear()
            } else {
                groups.other.replaceChildren()
            }
        }
        this.#setDisabled(true)
    }

    #getTreeselectController() {
        const especeWidget = this.especeWidget
        if (!especeWidget) return null
        return this.application.getControllerForElementAndIdentifier(especeWidget, "treeselect")
    }

    #populate({frequent, other}) {
        const groups = this.#groupContainers()
        if (!groups) return
        groups.frequent.replaceChildren(...frequent.map(it => this.#buildOption(it)))

        if (other.length > VIRTUALIZE_THRESHOLD) {
            if (!this.#virtualOther) {
                this.#virtualOther = new VirtualOptionList({
                    container: groups.other,
                    name: "espece",
                    onChange: input => this.#getTreeselectController()?.onChange({target: input}),
                })
                this.#getOtherGroupController()?.registerChild("virtual-other", this.#virtualOther)
            }
            this.#virtualOther.setItems(other)
        } else {
            if (this.#virtualOther) {
                this.#getOtherGroupController()?.unregisterChild("virtual-other")
            }
            this.#virtualOther = null
            groups.other.replaceChildren(...other.map(it => this.#buildOption(it)))
        }
    }

    #getOtherGroupController() {
        const groups = this.#groupContainers()
        const otherGroupEl = groups?.other.closest(".fr-treeselect__group")
        if (!otherGroupEl) return null
        return this.application.getControllerForElementAndIdentifier(otherGroupEl, "treeselect-group")
    }

    #buildOption({id, name}) {
        const template = document.getElementById(OPTION_TEMPLATE_ID)
        const inputId = `id_pre_creation_espece_option_${uid++}`
        const html = template.innerHTML
            .replaceAll("__id__", inputId)
            .replaceAll("__value__", escapeHTML(id))
            .replaceAll("__label__", escapeHTML(name))
        const container = document.createElement("div")
        container.innerHTML = html.trim()
        return container.firstElementChild
    }

    #groupContainers() {
        const especeWidget = this.especeWidget
        if (!especeWidget) return null
        const headers = [...especeWidget.querySelectorAll(".fr-treeselect__group-header")]
        const containerFor = label => {
            const header = headers.find(it => it.textContent.trim() === label)
            return header?.closest(".fr-treeselect__group")?.querySelector('[data-testid="group-container"]')
        }
        const frequent = containerFor(FREQUENT_GROUP_LABEL)
        const other = containerFor(OTHER_GROUP_LABEL)
        if (!frequent || !other) return null
        return {frequent, other}
    }

    #setDisabled(disabled) {
        this.#getTreeselectController()?.setDisabledState(disabled)
    }
}

applicationReady.then(app => app.register("espece-grouping", EspeceGrouping))
