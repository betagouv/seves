import {applicationReady} from "Application"
import {Controller} from "Stimulus"

class TypageFormController extends Controller {
    static targets = ["niveau2Select", "niveau3Select"]
    static values = {
        niveaux3ParNiveau2: Object,
    }

    connect() {
        this.refreshNiveau3Options()
    }

    onNiveau2Change() {
        this.refreshNiveau3Options()
    }

    refreshNiveau3Options() {
        if (!this.hasNiveau3SelectTarget) return
        const previousValue = this.niveau3SelectTarget.value
        const valeurs = this.niveaux3ParNiveau2Value[this.niveau2SelectTarget.value] || []

        this.niveau3SelectTarget.innerHTML = ""
        const placeholder = document.createElement("option")
        placeholder.value = ""
        placeholder.textContent = "Choisir dans la liste"
        this.niveau3SelectTarget.appendChild(placeholder)

        for (const valeur of valeurs) {
            const option = document.createElement("option")
            option.value = valeur
            option.textContent = valeur
            this.niveau3SelectTarget.appendChild(option)
        }

        this.niveau3SelectTarget.disabled = !valeurs.length
        if (valeurs.includes(previousValue)) {
            this.niveau3SelectTarget.value = previousValue
        }
    }
}

applicationReady.then(app => {
    app.register("typage-form", TypageFormController)
})
