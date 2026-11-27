import {applicationReady} from "Application"
import {BaseFormSetController} from "BaseFormset"
import {Controller} from "Stimulus"

let sharedIdentifiantPlaceholders = null

function getIdentifiantPlaceholders() {
    if (sharedIdentifiantPlaceholders === null) {
        const el = document.getElementById("espece-identifiant-placeholders")
        sharedIdentifiantPlaceholders = el ? JSON.parse(el.textContent) : {}
    }
    return sharedIdentifiantPlaceholders
}

class EspeceConcerneeRowController extends Controller {
    static targets = ["deleteInput", "especeField", "identifiantInput"]
    static values = {defaultPlaceholder: String}

    connect() {
        this.refreshIdentifiantPlaceholder()
    }

    get especeId() {
        const checked = this.especeFieldTarget.querySelector("input[type=radio]:checked")
        return checked ? checked.value : ""
    }

    onEspeceChange() {
        this.refreshIdentifiantPlaceholder()
    }

    refreshIdentifiantPlaceholder() {
        const placeholder = getIdentifiantPlaceholders()[this.especeId]
        this.identifiantInputTarget.placeholder = placeholder || this.defaultPlaceholderValue
    }

    onNumeroIdentifiantDetenteurChanged({detail: {value}}) {
        this.identifiantInputTarget.value = value
        this.notifyChanged()
    }

    onDelete() {
        this.deleteInputTarget.value = "on"
        this.element.classList.add("fr-hidden")
        this.notifyChanged()
    }

    notifyChanged() {
        this.dispatch("changed")
    }
}

applicationReady.then(app => {
    app.register("especes-concernees-formset", BaseFormSetController)
    app.register("especes-concernees-row", EspeceConcerneeRowController)
})
