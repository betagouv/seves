import {applicationReady} from "Application"
import {Controller} from "Stimulus"

class MassActionController extends Controller {
    static targets = [
        "navigation",
        "checkbox",
        "finSuiviModal",
        "finSuiviModalContent",
        "close",
        "cancel",
        "submit",
        "pkInput",
    ]
    static values = {apiUrl: String}

    syncNavDisabled() {
        this.navigationTarget.disabled = this.checkboxTargets.filter(checkbox => checkbox.checked).length === 0
    }

    onCheckboxChange() {
        this.syncNavDisabled()
    }

    onMasterCheckboxChange({target}) {
        this.checkboxTargets.forEach(checkbox => {
            checkbox.checked = target.checked
        })
        this.syncNavDisabled()
    }

    getCookie(name) {
        const value = `; ${document.cookie}`
        const parts = value.split(`; ${name}=`)
        if (parts.length === 2) return parts.pop().split(";").shift()
    }

    getSelectedElements() {
        return this.checkboxTargets.filter(checkbox => checkbox.checked).map(item => item.name)
    }

    showFinDeSuiviNotPossible(data, nbElements) {
        const html = `<div class="fr-alert fr-alert--info">
                      <p>Action impossible : aucun des événéments sélectionnés n'est éligible. Seul les événéments en cours peuvent faire l'objet d'une fin de suivi.</p>
                    </div>
                    `
        this.closeTarget.classList.remove("fr-hidden")
        this.finSuiviModalContentTarget.innerHTML = html
        dsfr(this.finSuiviModalTarget).modal.disclose()
    }

    showFinDeSuiviPossible(data, nbElements) {
        const html = `Vous êtes sur le point de signaler la fin de suivi de ${data.can_be_done} événements. Le suivi pourra être repris ultérieurement.`

        this.cancelTarget.classList.remove("fr-hidden")
        this.submitTarget.classList.remove("fr-hidden")
        this.finSuiviModalContentTarget.innerHTML = html
        this.pkInputTarget.value = this.getSelectedElements().join(",")
        dsfr(this.finSuiviModalTarget).modal.disclose()
    }

    showFinDeSuiviPartiallyPossible(data, nbElements) {
        let html = `<div class="fr-alert fr-alert--warning">
                              <p>${data.can_be_done} événements sur ${nbElements} peuvent faire l'objet de cette action. ${nbElements - data.can_be_done} sera/seront ignoré(s). Seuls les événéments en cours peuvent faire l'objet d'une fin de suivi.</p>
                            </div>`
        html += `<p class="fr-mt-2v">Vous êtes sur le point de signaler la fin de suivi de ${data.can_be_done} événements. Le suivi pourra être repris ultérieurement.</p>`

        this.cancelTarget.classList.remove("fr-hidden")
        this.submitTarget.classList.remove("fr-hidden")
        this.finSuiviModalContentTarget.innerHTML = html
        this.pkInputTarget.value = this.getSelectedElements().join(",")
        dsfr(this.finSuiviModalTarget).modal.disclose()
    }

    onFinDeSuivi() {
        const elements = this.getSelectedElements()
        const nbElements = elements.length
        fetch(this.apiUrlValue, {
            headers: {
                "Content-Type": "application/json",

                "X-CSRFToken": this.getCookie("csrftoken"),
            },
            method: "POST",
            body: JSON.stringify({action: "fin_suivi", pks: elements}),
        })
            .then(response => response.json())
            .then(data => {
                this.cancelTarget.classList.add("fr-hidden")
                this.closeTarget.classList.add("fr-hidden")
                this.submitTarget.classList.add("fr-hidden")
                this.pkInputTarget.value = ""
                if (data.can_be_done === 0) {
                    this.showFinDeSuiviNotPossible(data, nbElements)
                } else if (data.can_be_done === nbElements) {
                    this.showFinDeSuiviPossible(data, nbElements)
                } else {
                    this.showFinDeSuiviPartiallyPossible(data, nbElements)
                }
            })
    }
}

applicationReady.then(app => {
    app.register("mass-actions", MassActionController)
})
