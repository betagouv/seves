import {applicationReady} from "Application"
import {fetchAddress} from "BanAutocomplete"
import {Controller} from "Stimulus"

/**
 * ******** Targets ********
 * @property {HTMLSelectElement} etablissementAdresseTarget
 * @property {HTMLSelectElement} etablissementCommuneTarget
 * @property {HTMLInputElement} etablissementCodeInseeTarget
 * @property {HTMLSelectElement} particulierAdresseTarget
 * @property {HTMLSelectElement} particulierCommuneTarget
 * @property {HTMLInputElement} particulierCodeInseeTarget
 * @property {HTMLElement} particulierFieldsTarget
 * @property {HTMLButtonElement} reprendreAdresseBtnTarget
 * @property {HTMLElement} localisationAddressFieldsTarget
 */
class LocalisationFromDetenteurController extends Controller {
    static targets = [
        "etablissementAdresse",
        "etablissementCommune",
        "etablissementCodeInsee",
        "particulierAdresse",
        "particulierCommune",
        "particulierCodeInsee",
        "particulierFields",
        "reprendreAdresseBtn",
        "localisationAddressFields",
    ]

    #isParticulier = false

    /** @type {?MutationObserver} */
    #particulierFieldsObserver = null

    /** @return {AddressSearchAutocompleteController} */
    get localisationAddressOutlet() {
        return this.application.getControllerForElementAndIdentifier(
            this.localisationAddressFieldsTarget,
            "address-search-autocomplete",
        )
    }

    connect() {
        this.updateButtonState()
    }

    /** @param {HTMLElement} el */
    particulierFieldsTargetConnected(el) {
        this.#syncIsParticulier(el)
        this.#particulierFieldsObserver = new MutationObserver(() => this.#syncIsParticulier(el))
        this.#particulierFieldsObserver.observe(el, {attributes: true, attributeFilter: ["class"]})
    }

    particulierFieldsTargetDisconnected() {
        this.#particulierFieldsObserver?.disconnect()
        this.#particulierFieldsObserver = null
    }

    /** @param {HTMLElement} el */
    #syncIsParticulier(el) {
        this.#isParticulier = !el.classList.contains("fr-hidden")
        this.updateButtonState()
    }

    isParticulier() {
        return this.#isParticulier
    }

    detenteurAdresse() {
        return this.isParticulier() ? this.particulierAdresseTarget.value : this.etablissementAdresseTarget.value
    }

    detenteurCommune() {
        return this.isParticulier() ? this.particulierCommuneTarget.value : this.etablissementCommuneTarget.value
    }

    detenteurCodeInsee() {
        return this.isParticulier() ? this.particulierCodeInseeTarget.value : this.etablissementCodeInseeTarget.value
    }

    updateButtonState() {
        queueMicrotask(() => {
            this.reprendreAdresseBtnTarget.disabled = this.detenteurAdresse().trim() === ""
        })
    }

    async onReprendre() {
        const value = this.detenteurAdresse()
        const city = this.detenteurCommune()
        const inseeCode = this.detenteurCodeInsee()

        const query = [value, city].filter(Boolean).join(" ").trim()
        const results = query.length > 0 ? await fetchAddress(query) : undefined
        const bestMatch = results?.[0]?.customProperties

        this.localisationAddressOutlet.setAddress({
            value,
            city,
            inseeCode,
            postCode: bestMatch?.postCode,
            lat: bestMatch?.lat,
            long: bestMatch?.long,
        })
    }
}

applicationReady.then(app => {
    app.register("localisation-from-detenteur", LocalisationFromDetenteurController)
})
