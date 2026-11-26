import {applicationReady} from "Application"
import {Controller} from "Stimulus"

const pluralize = (count, singular, plural) => (count > 1 ? plural : singular)

/**
 * @property {HTMLButtonElement} navigationTarget
 * @property {HTMLInputElement[]} checkboxTargets
 * @property {HTMLInputElement} masterCheckboxTarget
 * @property {HTMLElement} selectionCountTarget
 * @property {HTMLElement} bannerTarget
 * @property {HTMLElement} bannerTextTarget
 * @property {HTMLButtonElement} selectAllFilteredButtonTarget
 * @property {HTMLButtonElement} clearSelectionButtonTarget
 * @property {HTMLDialogElement} finSuiviModalTarget
 * @property {HTMLDialogElement} clotureModalTarget
 * @property {string} apiUrlValue
 * @property {string} pksUrlValue
 * @property {number} totalCountValue
 */
class MassActionController extends Controller {
    static targets = [
        "navigation",
        "checkbox",
        "masterCheckbox",
        "selectionCount",
        "banner",
        "bannerText",
        "selectAllFilteredButton",
        "clearSelectionButton",
        "finSuiviModal",
        "clotureModal",
    ]
    static values = {apiUrl: String, pksUrl: String, totalCount: Number}

    /** @type {string[]|null} null until the selection is extended beyond the page */
    filteredPks = null
    excludedPks = new Set()

    get pagePks() {
        return this.checkboxTargets.filter(checkbox => checkbox.checked).map(checkbox => checkbox.name)
    }

    get selectedPks() {
        if (this.filteredPks) {
            return this.filteredPks.filter(pk => !this.excludedPks.has(pk))
        }
        return this.pagePks
    }

    connect() {
        this.render()
    }

    onCheckboxChange({target}) {
        if (this.filteredPks) {
            if (target.checked) {
                this.excludedPks.delete(target.name)
            } else {
                this.excludedPks.add(target.name)
            }
        }
        this.render()
    }

    onMasterCheckboxChange({target}) {
        if (!target.checked) {
            this.clearSelection()
            return
        }
        for (const checkbox of this.checkboxTargets) {
            checkbox.checked = true
            this.excludedPks.delete(checkbox.name)
        }
        this.render()
    }

    async selectAllFiltered() {
        const response = await fetch(this.pksUrlValue)
        const {pks} = await response.json()
        this.filteredPks = pks.map(String)
        // Checkboxes unchecked while loading stay excluded
        this.excludedPks = new Set(
            this.checkboxTargets.filter(checkbox => !checkbox.checked).map(checkbox => checkbox.name),
        )
        this.render()
    }

    clearSelection() {
        this.filteredPks = null
        this.excludedPks = new Set()
        for (const checkbox of this.checkboxTargets) {
            checkbox.checked = false
        }
        this.render()
    }

    render() {
        const count = this.selectedPks.length
        const nbPageChecked = this.pagePks.length
        const isPageChecked = nbPageChecked > 0 && nbPageChecked === this.checkboxTargets.length
        if (this.hasMasterCheckboxTarget) {
            this.masterCheckboxTarget.checked = isPageChecked
            this.masterCheckboxTarget.indeterminate = count > 0 && !isPageChecked
        }

        this.navigationTarget.disabled = count === 0
        this.selectionCountTarget.textContent =
            count > 0 ? `${count} ${pluralize(count, "événement sélectionné", "événements sélectionnés")}` : ""
        this.renderBanner(count, isPageChecked)
    }

    renderBanner(count, isPageChecked) {
        const canSelectAllFiltered =
            !this.filteredPks && isPageChecked && this.totalCountValue > this.checkboxTargets.length
        this.bannerTarget.classList.toggle("fr-hidden", !this.filteredPks && !canSelectAllFiltered)
        this.selectAllFilteredButtonTarget.classList.toggle("fr-hidden", !canSelectAllFiltered)
        this.clearSelectionButtonTarget.classList.toggle("fr-hidden", !this.filteredPks)

        if (this.filteredPks) {
            const nbFiltered = this.filteredPks.length
            this.bannerTextTarget.innerHTML =
                count === nbFiltered
                    ? `Les <strong>${nbFiltered} événements correspondant aux filtres</strong> sont sélectionnés.`
                    : `<strong>${count} des ${nbFiltered} événements correspondant aux filtres</strong> ${pluralize(count, "est sélectionné", "sont sélectionnés")}.`
        } else if (canSelectAllFiltered) {
            const nbOnPage = this.checkboxTargets.length
            this.bannerTextTarget.textContent = pluralize(
                nbOnPage,
                "L'événement de cette page est sélectionné.",
                `Les ${nbOnPage} événements de cette page sont sélectionnés.`,
            )
        }
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

    async onFinDeSuivi() {
        const selected = this.selectedPks.length
        const {can_be_done: nbEligibles} = await this.fetchStatus("fin_suivi")
        const rule = "Seuls les événements en cours peuvent faire l'objet d'une fin de suivi."

        if (nbEligibles === 0) {
            const subject =
                selected > 1
                    ? `aucun des ${selected} événements sélectionnés n'est éligible`
                    : "l'événement sélectionné n'est pas éligible"
            const html = `<div class="fr-alert fr-alert--info fr-alert--sm">
                <p>Action impossible : ${subject}. ${rule}</p>
            </div>`
            this.openModal(this.finSuiviModalTarget, html)
            return
        }

        let html = ""
        if (nbEligibles < selected) {
            const nbIgnored = selected - nbEligibles
            html += `<div class="fr-alert fr-alert--info fr-alert--sm fr-mb-2w">
                <p>${nbEligibles} des ${selected} événements sélectionnés ${pluralize(nbEligibles, "est éligible", "sont éligibles")} à la fin de suivi. ${nbIgnored} ${pluralize(nbIgnored, "sera ignoré", "seront ignorés")}. ${rule}</p>
            </div>`
        }
        html += `<p>Vous êtes sur le point de signaler la fin de suivi de ${nbEligibles} ${pluralize(nbEligibles, "événement", "événements")}. Le suivi pourra être repris ultérieurement.</p>`
        this.openModal(this.finSuiviModalTarget, html, true)
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
