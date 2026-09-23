import {applicationReady} from "Application"
import {Controller} from "Stimulus"

class InformationsController extends Controller {
    static targets = ["statutInput", "dateInput"]

    connect() {
        document.addEventListener("resultConfirmed", () => {
            this.statutInputTarget.value = "CONFIRME"
            this.dateInputTarget.value = new Date().toLocaleDateString("sv-SE", {timeZone: "Europe/Paris"})
        })
    }
}

applicationReady.then(app => {
    app.register("informations-form", InformationsController)
})
