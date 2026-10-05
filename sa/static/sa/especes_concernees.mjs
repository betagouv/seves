import {applicationReady} from "Application"
import {BaseFormSetController} from "BaseFormset"
import {Controller} from "Stimulus"

class EspeceConcerneeRowController extends Controller {
    static targets = ["deleteInput"]

    onDelete() {
        this.deleteInputTarget.value = "on"
        this.element.classList.add("fr-hidden")
    }
}

applicationReady.then(app => {
    app.register("especes-concernees-formset", BaseFormSetController)
    app.register("especes-concernees-row", EspeceConcerneeRowController)
})
