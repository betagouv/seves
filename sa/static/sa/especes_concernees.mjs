import {applicationReady} from "Application"
import {BaseFormSetController} from "BaseFormset"
import {Controller} from "Stimulus"
import {VirtualOptionList} from "VirtualOptionList"

const OTHER_GROUP_LABEL = "Autres"

let autresEspeces = null

function getAutresEspeces() {
    if (autresEspeces === null) {
        const el = document.getElementById("especes-concernees-autres")
        autresEspeces = el ? JSON.parse(el.textContent) : []
    }
    return autresEspeces
}

class EspeceConcerneeRowController extends Controller {
    static targets = ["deleteInput"]

    onDelete() {
        this.deleteInputTarget.value = "on"
        this.element.classList.add("fr-hidden")
    }
}

/**
 * As "Autres" group contains quite a lot of especes, it is only rendered server-side with the selected espece,
 * and is filled with a virtualized listthe first time the widget is used.
 * @property {String} nameValue
 */
class EspeceConcerneeEspeceController extends Controller {
    static values = {name: String}

    #virtualOther = null

    get treeselectElement() {
        return this.element.querySelector('[data-controller~="treeselect"]')
    }

    loadAutres() {
        if (this.#virtualOther) return

        const treeselectElement = this.treeselectElement
        const otherGroup = [...treeselectElement.querySelectorAll(".fr-treeselect__group")].find(
            it => it.querySelector(".fr-treeselect__group-header")?.textContent.trim() === OTHER_GROUP_LABEL,
        )
        const container = otherGroup?.querySelector('[data-testid="group-container"]')
        if (!container) return

        const treeselect = this.application.getControllerForElementAndIdentifier(treeselectElement, "treeselect")
        const checked = [...container.querySelectorAll("input:checked")].map(it => it.value)
        this.#virtualOther = new VirtualOptionList({
            container,
            name: this.nameValue,
            onChange: input => treeselect?.onChange({target: input}),
            treeselectElement,
        })
        this.#virtualOther.setItems(getAutresEspeces())
        this.#virtualOther.setChecked(checked)
        this.application
            .getControllerForElementAndIdentifier(otherGroup, "treeselect-group")
            ?.registerChild("virtual-other", this.#virtualOther)
    }
}

applicationReady.then(app => {
    app.register("especes-concernees-formset", BaseFormSetController)
    app.register("especes-concernees-row", EspeceConcerneeRowController)
    app.register("especes-concernees-espece", EspeceConcerneeEspeceController)
})
