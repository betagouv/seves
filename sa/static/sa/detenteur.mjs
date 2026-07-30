import {applicationReady} from "Application"
import {Controller} from "Stimulus"

class DetenteurFormController extends Controller {
    static targets = ["etablissementForm", "particulierForm", "numeroIdentifiantEtablissement", "nomParticulier"]

    connect() {
        this.showEtablissement()
    }

    showEtablissement() {
        this.etablissementFormTarget.classList.remove("fr-hidden")
        this.numeroIdentifiantEtablissementTarget.required = true

        this.particulierFormTarget.classList.add("fr-hidden")
        this.nomParticulierTarget.required = false
    }

    showParticulier() {
        this.etablissementFormTarget.classList.add("fr-hidden")
        this.numeroIdentifiantEtablissementTarget.required = false

        this.particulierFormTarget.classList.remove("fr-hidden")
        this.nomParticulierTarget.required = true
    }
}

applicationReady.then(app => {
    app.register("detenteur-form", DetenteurFormController)
})
