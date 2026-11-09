import {applicationReady} from "Application"
import {Controller} from "Stimulus"

const pluralize = (count, singular, plural) => (count > 1 ? plural : singular)

/**
 * @property {HTMLButtonElement} navigationTarget
 * @property {HTMLInputElement[]} checkboxTargets
 * @property {HTMLInputElement} masterCheckboxTarget
 * @property {HTMLElement} selectionCountTarget
 * @property {HTMLDialogElement} finSuiviModalTarget
 * @property {HTMLDialogElement} clotureModalTarget
 * @property {string} apiUrlValue
 */
class MassActionController extends Controller {
    static targets = ["navigation", "checkbox", "masterCheckbox", "selectionCount", "finSuiviModal", "clotureModal"]
    static values = {apiUrl: String}

    get selectedPks() {
        return this.checkboxTargets.filter(checkbox => checkbox.checked).map(checkbox => checkbox.name)
    }

    connect() {
        this.render()
    }

    onCheckboxChange() {
        this.render()
    }

    onMasterCheckboxChange({target}) {
        for (const checkbox of this.checkboxTargets) {
            checkbox.checked = target.checked
        }
        this.render()
    }

    render() {
        const count = this.selectedPks.length
        const isPageChecked = count > 0 && count === this.checkboxTargets.length
        if (this.hasMasterCheckboxTarget) {
            this.masterCheckboxTarget.checked = isPageChecked
            this.masterCheckboxTarget.indeterminate = count > 0 && !isPageChecked
        }

        this.navigationTarget.disabled = count === 0
        this.selectionCountTarget.textContent =
            count > 0 ? `${count} ${pluralize(count, "événement sélectionné", "événements sélectionnés")}` : ""
    }

    getCookie(name) {
        const value = `; ${document.cookie}`
        const parts = value.split(`; ${name}=`)
        if (parts.length === 2) return parts.pop().split(";").shift()
    }

    async fetchStatus(action) {
        const response = await fetch(this.apiUrlValue, {
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": this.getCookie("csrftoken"),
            },
            method: "POST",
            body: JSON.stringify({action, pks: this.selectedPks}),
        })
        return response.json()
    }

    /**
     * @param {HTMLDialogElement} modal
     * @param {string} html
     * @param {boolean} canSubmit False when none of the selected evenements is eligible
     */
    openModal(modal, html, canSubmit = false) {
        const find = name => modal.querySelector(`[data-mass-actions-target="${name}"]`)
        find("modalContent").innerHTML = html
        find("pkInput").value = canSubmit ? this.selectedPks.join(",") : ""
        find("close").classList.toggle("fr-hidden", canSubmit)
        find("cancel").classList.toggle("fr-hidden", !canSubmit)
        find("submit").classList.toggle("fr-hidden", !canSubmit)
        dsfr(modal).modal.disclose()
    }

    showFinDeSuiviNotPossible() {
        const html = `<div class="fr-alert fr-alert--info">
                      <p>Action impossible : aucun des événéments sélectionnés n'est éligible. Seul les événéments en cours peuvent faire l'objet d'une fin de suivi.</p>
                    </div>
                    `
        this.openModal(this.finSuiviModalTarget, html)
    }

    showFinDeSuiviPossible(data) {
        const html = `Vous êtes sur le point de signaler la fin de suivi de ${data.can_be_done} événements. Le suivi pourra être repris ultérieurement.`
        this.openModal(this.finSuiviModalTarget, html, true)
    }

    showFinDeSuiviPartiallyPossible(data, nbElements) {
        let html = `<div class="fr-alert fr-alert--warning">
                              <p>${data.can_be_done} événements sur ${nbElements} peuvent faire l'objet de cette action. ${nbElements - data.can_be_done} sera/seront ignoré(s). Seuls les événéments en cours peuvent faire l'objet d'une fin de suivi.</p>
                            </div>`
        html += `<p class="fr-mt-2v">Vous êtes sur le point de signaler la fin de suivi de ${data.can_be_done} événements. Le suivi pourra être repris ultérieurement.</p>`
        this.openModal(this.finSuiviModalTarget, html, true)
    }

    async onFinDeSuivi() {
        const nbElements = this.selectedPks.length
        const data = await this.fetchStatus("fin_suivi")
        if (data.can_be_done === 0) {
            this.showFinDeSuiviNotPossible()
        } else if (data.can_be_done === nbElements) {
            this.showFinDeSuiviPossible(data)
        } else {
            this.showFinDeSuiviPartiallyPossible(data, nbElements)
        }
    }

    async onCloture() {
        const selected = this.selectedPks.length
        const data = await this.fetchStatus("cloture")
        const {can_be_done: nbEligibles, not_in_fin_suivi: nbNotInFinSuivi} = data
        const ineligibles = [
            [data.draft, "brouillon", "brouillons"],
            [data.already_cloture, "déjà clôturé", "déjà clôturés"],
        ]
            .filter(([count]) => count > 0)
            .map(([count, singular, plural]) => `${count} ${pluralize(count, singular, plural)}`)
            .join(", ")

        if (nbEligibles === 0) {
            const subject =
                selected > 1
                    ? `aucun des ${selected} événements sélectionnés n'est éligible`
                    : "l'événement sélectionné n'est pas éligible"
            const html = `<div class="fr-alert fr-alert--info fr-alert--sm">
                <p>Action impossible : ${subject} (${ineligibles}). Seuls les événements en cours ou en fin de suivi peuvent être clôturés.</p>
            </div>`
            this.openModal(this.clotureModalTarget, html)
            return
        }

        let html = ""
        const qualifier = nbEligibles < selected ? "éligible" : "sélectionné"
        if (nbEligibles < selected) {
            html += `<div class="fr-alert fr-alert--info fr-alert--sm fr-mb-2w">
                <p>${nbEligibles} des ${selected} événements sélectionnés ${pluralize(nbEligibles, "est éligible", "sont éligibles")} à la clôture. Les autres (${ineligibles}) ne seront pas modifiés.</p>
            </div>`
        }
        if (nbNotInFinSuivi > 0) {
            const evenements =
                nbEligibles > 1
                    ? `${nbNotInFinSuivi} des ${nbEligibles} événements ${qualifier}s`
                    : `l'événement ${qualifier}`
            html += `<div class="fr-alert fr-alert--warning fr-alert--sm fr-mb-2w">
                <p>Attention, pour ${evenements}, une ou plusieurs structures concernées n'ont pas signalé la fin de leur suivi.</p>
            </div>
            <p>Souhaitez-vous tout de même procéder à la clôture de ${pluralize(nbEligibles, "cet événement", "ces événements")} ?</p>`
        } else {
            html += `<p>Vous êtes sur le point de clôturer ${nbEligibles} ${pluralize(nbEligibles, "événement", "événements")}. Confirmez-vous cette action ?</p>`
        }
        this.openModal(this.clotureModalTarget, html, true)
    }
}

applicationReady.then(app => {
    app.register("mass-actions", MassActionController)
})
