import {applicationReady} from "Application"
import {setUpAddressChoices} from "BanAutocomplete"
import {setUpCommuneChoices} from "Commune"
import {Controller} from "Stimulus"

/**
 * ******** Targets ********
 * @property {HTMLSelectElement[]} addressTargets
 * @property {HTMLSelectElement[]} communeTargets
 * @property {HTMLInputElement[]} codeInseeTargets
 * @property {HTMLInputElement[]} codePostalTargets
 * @property {HTMLSelectElement[]} departementTargets
 * @property {HTMLInputElement[]} countryTargets
 * @property {HTMLInputElement[]} latitudeTargets
 * @property {HTMLInputElement[]} longitudeTargets
 */
class AddressSearchAutocompleteController extends Controller {
    static targets = [
        "address",
        "commune",
        "codeInsee",
        "codePostal",
        "departement",
        "country",
        "latitude",
        "longitude",
    ]

    /** @type {?Choices} */
    addressWidget = null

    /** @type {?Choices} */
    communeWidget = null

    addressTargetConnected(el) {
        this.addressWidget = setUpAddressChoices(el)
        el.dataset.action = [
            ...(el.dataset.action || "").split(/\s+/g).filter(Boolean),
            `choice->${this.identifier}#onAddressChoice`,
        ].join(" ")
    }

    addressTargetDisconnected() {
        this.addressWidget?.destroy()
        this.addressWidget = null
    }

    communeTargetConnected(el) {
        this.communeWidget = setUpCommuneChoices(el)
        el.dataset.action = [
            ...(el.dataset.action || "").split(/\s+/g).filter(Boolean),
            `choice->${this.identifier}#onCommuneChoice`,
            `removeItem->${this.identifier}#onRemoveItem`,
            `forcedChoice->${this.identifier}#onCommuneForcedChoice`,
        ].join(" ")
    }

    communeTargetDisconnected() {
        this.communeWidget?.destroy()
        this.communeWidget = null
    }

    setAddress(data) {
        const departementCode = (data.context || "").split(",")[0].trim()
        if (data.value) {
            this.addressWidget?.setValue([data.value])
        }
        this.communeWidget?.setValue([data.city])
        const fieldsToUpdate = [
            [this.departementTargets, departementCode],
            [this.communeTargets, data.city],
            [this.codeInseeTargets, data.inseeCode],
            [this.codePostalTargets, data.postCode],
            [this.latitudeTargets, data.lat],
            [this.longitudeTargets, data.long],
        ]
        if (data.context !== undefined && data.context !== null) {
            fieldsToUpdate.push([this.countryTargets, "FR"])
        }
        this.#updateFields(fieldsToUpdate)
    }

    onCommuneChoice({detail: {value, customProperties}}) {
        this.#updateFields([
            [this.communeTargets, value],
            [this.codeInseeTargets, customProperties.inseeCode],
            [this.codePostalTargets, customProperties.postCode],
            [this.departementTargets, customProperties.departementCode],
        ])
    }

    onCommuneForcedChoice({detail: {value}}) {
        this.communeWidget?.setValue([value])
    }

    onAddressChoice({detail: {customProperties}}) {
        this.setAddress(customProperties)
    }

    onRemoveItem() {
        this.#updateFields([
            [this.departementTargets, ""],
            [this.communeTargets, ""],
            [this.codeInseeTargets, ""],
            [this.codePostalTargets, ""],
        ])
    }

    /** @param {[HTMLElement[], any][]} fieldsAndValues */
    #updateFields(fieldsAndValues) {
        for (const [elts, value] of fieldsAndValues) {
            if (value === undefined || value === null) continue
            for (const it of elts) {
                it.value = value
                if (it instanceof HTMLInputElement) {
                    it.dispatchEvent(new Event("input"))
                } else {
                    it.dispatchEvent(new Event("change"))
                }
            }
        }
    }
}

applicationReady.then(app => {
    app.register("address-search-autocomplete", AddressSearchAutocompleteController)
})
