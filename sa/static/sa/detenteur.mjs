import {applicationReady} from "Application"
import {resetForm} from "Forms"
import {Controller} from "Stimulus"
import {setUpSiretChoices} from "siret"

class DetenteurFormController extends Controller {
    static targets = [
        "etablissementForm",
        "particulierForm",
        "numeroIdentifiantEtablissement",
        "nomParticulier",
        "etablissementRadio",
        "particulierRadio",
        "confirmModal",
        "siretEtablissement",
        "raisonSocialeInput",
    ]

    /** @type {?Choices} */
    #sireneWidget = null

    /** @return {AddressSearchAutocompleteController} */
    get etablissementAddressOutlet() {
        return this.application.getControllerForElementAndIdentifier(
            this.etablissementFormTarget,
            "address-search-autocomplete",
        )
    }

    connect() {
        this.currentType = this.particulierRadioTarget.checked ? "particulier" : "etablissement"
        // Type we're about to switch to, waiting for confirmation in the modal
        this.pendingType = null
        if (this.currentType === "particulier") {
            this.showParticulier()
        } else {
            this.showEtablissement()
        }
        this.confirmModalTarget.addEventListener("close", () => {
            this.pendingType = null
        })
    }

    onEtablissementLabelClick(event) {
        this.handleTypeClick(event, "etablissement")
    }

    onParticulierLabelClick(event) {
        this.handleTypeClick(event, "particulier")
    }

    handleTypeClick(event, type) {
        if (type === this.currentType) {
            return
        }
        if (this.currentBlockHasData()) {
            // preventDefault prevents the click on the <label> from checking its radio input:
            // the switch only happens once the user confirms in the modal
            event.preventDefault()
            this.pendingType = type
            dsfr(this.confirmModalTarget).modal.disclose()
        } else {
            this.switchTo(type)
        }
    }

    onConfirmSwitch() {
        resetForm(this.currentType === "etablissement" ? this.etablissementFormTarget : this.particulierFormTarget)
        this.switchTo(this.pendingType)
        this.pendingType = null
        dsfr(this.confirmModalTarget).modal.conceal()
    }

    onCancelSwitch() {
        this.pendingType = null
        dsfr(this.confirmModalTarget).modal.conceal()
    }

    switchTo(type) {
        this.currentType = type
        // Check the radio manually (as the native check was prevented in handleTypeClick)
        if (type === "etablissement") {
            this.etablissementRadioTarget.checked = true
            this.showEtablissement()
        } else {
            this.particulierRadioTarget.checked = true
            this.showParticulier()
        }
    }

    currentBlockHasData() {
        const target = this.currentType === "etablissement" ? this.etablissementFormTarget : this.particulierFormTarget
        return [...target.querySelectorAll("input, select, textarea")].some(field => field.value.trim() !== "")
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

    siretEtablissementTargetConnected(el) {
        this.#sireneWidget = setUpSiretChoices(el, "top")
    }

    siretEtablissementTargetDisconnected() {
        this.#sireneWidget?.destroy()
        this.#sireneWidget = null
    }

    onSireneChoice({detail: {customProperties}}) {
        this.etablissementAddressOutlet.setAddress({
            value: customProperties.streetData,
            context: customProperties.code_commune?.substring(0, 2),
            city: customProperties.commune,
            inseeCode: customProperties.code_commune,
            postCode: customProperties.code_postal,
        })
        if (customProperties.raison) {
            this.raisonSocialeInputTarget.value = customProperties.raison
        }
    }
}

applicationReady.then(app => {
    app.register("detenteur-form", DetenteurFormController)
})
