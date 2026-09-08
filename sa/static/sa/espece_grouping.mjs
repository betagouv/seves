import {applicationReady} from "Application"
import {Controller} from "Stimulus"

const FREQUENT_GROUP_LABEL = "Les plus fréquentes"
const OTHER_GROUP_LABEL = "Autres"
const ESPECE_WIDGET_ID = "fr-treeselect-id_pre_creation_espece"
const ESPECE_FIELD_NAME = "espece"

let uid = 0

class EspeceGrouping extends Controller {
    static targets = ["maladieInput"]

    #byMaladie = {}

    initialize() {
        this.#byMaladie = JSON.parse(this.element.querySelector("#espece-options-by-maladie")?.innerText ?? "{}")
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
        const options = this.#byMaladie[target.value]
        if (!options) {
            this.#clear()
            return
        }
        this.#populate(options)
        this.#setDisabled(false)
    }

    #clear() {
        this.#getTreeselectController()?.unselectAll()
        const groups = this.#groupContainers()
        if (groups) {
            groups.frequent.replaceChildren()
            groups.other.replaceChildren()
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
        groups.other.replaceChildren(...other.map(it => this.#buildOption(it)))
    }

    #buildOption({id, name}) {
        const wrapper = document.createElement("div")
        wrapper.className = "fr-treeselect__element"
        wrapper.dataset.controller = "treeselect-element"

        const radioGroup = document.createElement("div")
        radioGroup.className = "fr-radio-group"

        const input = document.createElement("input")
        input.type = "radio"
        input.name = ESPECE_FIELD_NAME
        input.id = `id_pre_creation_espece_option_${uid++}`
        input.value = String(id)
        input.dataset.action = "change->treeselect#onChange"

        const label = document.createElement("label")
        label.className = "fr-label"
        label.htmlFor = input.id
        label.textContent = name

        radioGroup.append(input, label)
        wrapper.append(radioGroup)
        return wrapper
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
        const especeWidget = this.especeWidget
        if (!especeWidget) return
        especeWidget.classList.toggle("fr-treeselect--disabled", disabled)
        const button = especeWidget.querySelector(".fr-treeselect__button")
        if (button) button.disabled = disabled
    }
}

applicationReady.then(app => app.register("espece-grouping", EspeceGrouping))
