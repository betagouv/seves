import {applicationReady} from "Application"
import {Controller} from "Stimulus"

class InformationsController extends Controller {
    static targets = ["statutInput", "dateInput"]

    connect() {
        document.addEventListener("resultConfirmed", event => {
            this.statutInputTarget.value = "CONFIRME"
            this.dateInputTarget.value = event.detail.date
        })
    }
}

applicationReady.then(app => {
    app.register("informations-form", InformationsController)
})
