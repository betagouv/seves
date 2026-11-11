import {applicationReady} from "Application"
import {Controller} from "Stimulus"

const plural = (count, singular, plural) => (count > 1 ? plural : singular)

const ACTIONS = {
    fin_suivi: {
        mode: "add",
        title: "Signaler une fin de suivi",
        submit: `<span class="ri-notification-off-fill fr-mr-2v" aria-hidden="true"></span>Signaler la fin de suivi`,
        eligibility: "Seuls les événements en cours peuvent faire l'objet d'une fin de suivi.",
        confirmation: canBeDone =>
            `Vous êtes sur le point de signaler la fin de suivi de ${canBeDone} ${plural(canBeDone, "événement", "événements")}. Le suivi pourra être repris ultérieurement.`,
    },
    reprise_suivi: {
        mode: "remove",
        title: "Reprendre le suivi",
        submit: `<span class="ri-notification-2-fill fr-mr-2v" aria-hidden="true"></span>Reprendre le suivi`,
        eligibility:
            "Seuls les événements en fin de suivi peuvent reprendre le suivi. Un événement clôturé ne peut pas être rouvert.",
        confirmation: canBeDone =>
            `Vous êtes sur le point de reprendre le suivi de ${canBeDone} ${plural(canBeDone, "événement. Son statut", "événements. Leur statut")} redeviendra « En cours ».`,
    },
}

class MassActionController extends Controller {
    static targets = [
        "navigation",
        "checkbox",
        "modal",
        "modalTitle",
        "modalContent",
        "close",
        "cancel",
        "submit",
        "modeInput",
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

    getModalContent(action, canBeDone, nbElements) {
        if (canBeDone === 0) {
            const selection = plural(
                nbElements,
                "l'événement sélectionné n'est pas éligible",
                `aucun des ${nbElements} événements sélectionnés n'est éligible`,
            )
            return `<div class="fr-alert fr-alert--info">
                        <p>Action impossible : ${selection}. ${action.eligibility}</p>
                    </div>`
        }

        let html = ""
        if (canBeDone < nbElements) {
            const ignored = nbElements - canBeDone
            html += `<div class="fr-alert fr-alert--warning">
                         <p>${canBeDone} ${plural(canBeDone, "événement", "événements")} sur ${nbElements} ${plural(canBeDone, "peut", "peuvent")} faire l'objet de cette action. ${ignored} ${plural(ignored, "sera ignoré", "seront ignorés")}. ${action.eligibility}</p>
                     </div>`
        }
        html += `<p class="fr-mt-2v">${action.confirmation(canBeDone)}</p>`
        return html
    }

    showModal(action, canBeDone, nbElements) {
        const canBeSubmitted = canBeDone > 0
        this.modalTitleTarget.textContent = action.title
        this.modalContentTarget.innerHTML = this.getModalContent(action, canBeDone, nbElements)
        this.submitTarget.innerHTML = action.submit
        this.modeInputTarget.value = action.mode
        this.pkInputTarget.value = canBeSubmitted ? this.getSelectedElements().join(",") : ""
        this.closeTarget.classList.toggle("fr-hidden", canBeSubmitted)
        this.cancelTarget.classList.toggle("fr-hidden", !canBeSubmitted)
        this.submitTarget.classList.toggle("fr-hidden", !canBeSubmitted)
        dsfr(this.modalTarget).modal.disclose()
    }

    onMassAction({params: {action}}) {
        const elements = this.getSelectedElements()
        fetch(this.apiUrlValue, {
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": this.getCookie("csrftoken"),
            },
            method: "POST",
            body: JSON.stringify({action, pks: elements}),
        })
            .then(response => response.json())
            .then(data => this.showModal(ACTIONS[action], data.can_be_done, elements.length))
    }
}

applicationReady.then(app => {
    app.register("mass-actions", MassActionController)
})
