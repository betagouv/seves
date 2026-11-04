import {applicationReady} from "Application"
import {BaseFormSetController} from "BaseFormset"
import {Controller} from "Stimulus"

class EspeceConcerneeRowController extends Controller {
    static targets = ["deleteInput", "especeField", "identifiantInput"]

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
