import {applicationReady} from "Application"
import {Controller} from "Stimulus"

class EvenementSimpleController extends Controller {
    static targets = ["notice", "noticeEvenementProduit", "noticeTransfer"]

    onFollowUpChange(event) {
        if (event.target.value === "investigation tiac") {
            this.noticeTarget.classList.remove("fr-hidden")
        } else {
            this.noticeTarget.classList.add("fr-hidden")
        }
        if (event.target.value === "passe en evenement produit") {
            this.noticeEvenementProduitTarget.classList.remove("fr-hidden")
        } else {
            this.noticeEvenementProduitTarget.classList.add("fr-hidden")
        }
        if (event.target.value === "programmation a une autre DD") {
            this.noticeTransferTarget.classList.remove("fr-hidden")
        } else {
            this.noticeTransferTarget.classList.add("fr-hidden")
        }
    }
}

applicationReady.then(app => {
    app.register("evenement-simple-form", EvenementSimpleController)
})
