import {applicationReady, escapeHTML} from "Application"
import {setUpAddressChoices} from "BanAutocomplete"
import {BaseFormInModal} from "BaseFormInModal"
import {BaseFormSetController} from "BaseFormset"
import {setUpCommuneChoices} from "Commune"
import {collectFormValues} from "Forms"
import {Controller} from "Stimulus"
import {createStore, useStore} from "StimulusStore"
import {setUpSiretChoices} from "siret"

/**
 * @typedef LieuData
 * @property {string} nom
 * @property {string} site_inspection
 * @property {string} adresse_lieu_dit
 * @property {string} code_insee
 * @property {string} code_postal
 * @property {string} commune
 * @property {string} departement
 * @property {string} wgs84_latitude
 * @property {string} wgs84_longitude
 * @property {string} position_chaine_distribution_etablissement
 */

const lieuxStore = createStore({
    name: "lieuxStore",
    type: Object,
    initialValue: {},
})

const prelevementsStore = createStore({
    name: "prelevementsStore",
    type: Array,
    initialValue: [],
})

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
    #addressWidget = null

    /** @type {?Choices} */
    #communeWidget = null

    addressTargetConnected(el) {
        this.#addressWidget = setUpAddressChoices(el)
        el.dataset.action = [
            ...(el.dataset.action || "").split(/s+/g),
            `choice->${this.identifier}#onAddressChoice`,
        ].join(" ")
    }

    addressTargetDisconnected() {
        this.#addressWidget?.destroy()
        this.#addressWidget = null
    }

    communeTargetConnected(el) {
        this.#communeWidget = setUpCommuneChoices(el)
        el.dataset.action = [
            ...(el.dataset.action || "").split(/s+/g),
            `choice->${this.identifier}#onCommuneChoice`,
            `removeItem->${this.identifier}#onRemoveItem`,
            `forcedChoice->${this.identifier}#onCommuneForcedChoice`,
        ].join(" ")
    }

    communeTargetDisconnected() {
        this.#communeWidget?.destroy()
        this.#communeWidget = null
    }

    setAddress(data) {
        const departementCode = (data.context || "").split(",")[0].trim()
        if (data.value) {
            this.#addressWidget?.setValue([data.value])
        }
        this.#communeWidget?.setValue([data.city])
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
        this.#communeWidget?.setValue([value])
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

/**
 * ******** Targets ********
 * @property {HTMLElement[]} errorMessageTargets
 * @property {HTMLInputElement} nomInputTarget
 * @property {HTMLSelectElement} sireneSelectTarget
 * @property {HTMLElement} etablissementFieldsTarget
 * @property {HTMLInputElement} raisonSocialeInputTarget
 * @property {HTMLInputElement} activiteEtablissementInputTarget
 * @property {HTMLParagraphElement} charCounterTarget
 * ******** Values ********
 * @property {boolean} isValidValue
 * ******** Stores ********
 * @property  {function(value: import("StimulusStore/dist/types/setCallback").SetCallback)}  setLieuxStoreValue
 * @property  {import("StimulusStore/dist/types/updateMethod").UpdateMethod}  onLieuxStoreUpdate
 * @property {Object} lieuxStoreValue
 *
 * @property  {function(value: import("StimulusStore/dist/types/setCallback").SetCallback)}  setPrelevementsStoreValue
 * @property  {import("StimulusStore/dist/types/updateMethod").UpdateMethod}  onPrelevementsStoreUpdate
 * @property {PrelevementData[]} prelevementsStoreValue
 * ******** Outlets ********
 * @property {ModalController} removeImpossibleModalOutlet
 */
class LieuFormController extends BaseFormInModal {
    static targets = [
        "errorMessage",
        "nomInput",
        "sireneSelect",
        "etablissementFields",
        "raisonSocialeInput",
        "activiteEtablissementInput",
        "charCounter",
    ]
    static values = {isValid: {type: Boolean, default: true}}
    static stores = [lieuxStore, prelevementsStore]

    /** @type {?Choices} */
    #sireneWidget = null

    /** @return {AddressSearchAutocompleteController} */
    get etablissementAddressOutlet() {
        return this.application.getControllerForElementAndIdentifier(
            this.etablissementFieldsTarget,
            "address-search-autocomplete",
        )
    }

    /** @return {ModalController} */
    get removeImpossibleModalOutlet() {
        return this.application.getControllerForElementAndIdentifier(
            document.querySelector("#fr-modal-suppression-lieu"),
            "modal",
        )
    }

    connect() {
        useStore(this)

        if (this.shouldImmediatelyShowValue) {
            this.openDialog()
        } else {
            this.initCard(
                collectFormValues(this.fieldsetTarget, {
                    nameTransform: name => name.replace(`${this.formPrefixValue}-`, ""),
                    skipValidation: true,
                }),
            )
        }
    }

    sireneSelectTargetConnected(el) {
        this.#sireneWidget = setUpSiretChoices(el, "top")
    }

    sireneSelectTargetDiconnected() {
        this.#sireneWidget?.destroy()
        this.#sireneWidget = null
    }

    /** @param {HTMLTextAreaElement} el*/
    activiteEtablissementInputTargetConnected(el) {
        el.dispatchEvent(new Event("input"))
    }

    /** @param {LieuData} lieu */
    initCard(lieu) {
        this.shouldImmediatelyShowValue = false
        this.cardContainerTargets.forEach(it => it.remove())
        this.element.insertAdjacentHTML("beforeend", this.renderCard(lieu))
        this.element.insertAdjacentHTML("beforeend", this.renderDeleteConfirmationDialog(lieu))
        this.setLieuxStoreValue(value => ({...value, [this.formPrefixValue]: lieu}))
        dsfr(this.dialogTarget).modal.conceal()
    }

    forceDelete() {
        super.forceDelete()
        this.setLieuxStoreValue(value => {
            delete value[this.formPrefixValue]
            return value
        })
    }

    getDeleteConfirmationSentence(_data) {
        return "Souhaitez-vous réellement supprimer le lieu ?"
    }

    getDeleteConfirmationTitle(_data) {
        return "Suppression d'un lieu"
    }

    onDelete() {
        if (this.prelevementsStoreValue.find(it => it.lieu.trim() === this.nomInputTarget.value.trim())) {
            this.removeImpossibleModalOutlet.disclose()
            return
        }
        super.onDelete()
    }

    onCloseForm() {
        // this.shouldImmediatelyShowValue indicates that the card has not be rendered yet.
        // In this case, the form is not considered valid and it should be deleted on close
        if (this.shouldImmediatelyShowValue) this.forceDelete()
        this.errorMessageTargets.forEach(it => it.remove())
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

    onActiviteEtablissementChange({target: {value}}) {
        this.charCounterTarget.textContent = `${Math.max(100 - value.trim().length, 0)} caractères restants`
    }

    /**
     * @param {LieuData} lieu
     * @return {string}
     */
    renderCard(lieu) {
        const hasErrors = !this.isValidValue
        let lieuCommune = this.optionalText(
            lieu.commune,
            this.joinText(
                "",
                lieu.commune,
                this.optionalText(lieu.code_postal, ` (${lieu.code_postal})`),
                this.optionalText(lieu.departement, ` | ${lieu.departement.replaceAll(/^\s*\w+\s*-\s*/g, "")}`),
            ),
        ).trim()
        lieuCommune = lieuCommune !== "" ? lieuCommune : this.optionalText(lieu.departement)

        // language=HTML
        return `<section id="${this.formPrefixValue}--card" class="seves-card" data-${this.identifier}-target="cardContainer">
            ${this.optionalText(
                hasErrors,
                `<div id="${this.formPrefixValue}--error-desc" class="fr-alert fr-alert--error fr-mb-2v" aria-live="polite" data-${this.identifier}-target="errorMessage">
                    <p>Ce formulaire contient des erreurs. Veuillez l'éditer pour les corriger</p>
                </div>`,
            )}
            <div class="fr-card"${this.optionalText(hasErrors, ` aria-labelledby="${this.formPrefixValue}--error-desc"`)} data-testid="lieu-initial">
                <div class="fr-card__body">
                    <div class="fr-card__content">
                        <h3
                            class="fr-card__title"
                            data-${this.identifier}-target="denomination"
                            aria-labelledby="${this.formPrefixValue}--button-open-modal"
                        >
                            <button
                                id="${this.formPrefixValue}--button-open-modal"
                                class="fr-link"
                                type="button"
                                data-action="${this.identifier}#onModify:prevent:default"
                            >
                                ${lieu.nom}
                            </button>
                        </h3>
                        <div class="fr-card__desc fr-mt-4v fr-flex fr-flex--gap-2v">
                            ${this.joinText(lieuCommune, `<p class="fr-card__detail fr-icon-map-pin-2-line">${escapeHTML(lieuCommune)}</p>`)}
                            <section>
                                ${this.renderBadges([lieu.site_inspection, lieu.position_chaine_distribution_etablissement])}
                            </section>
                        </div>
                        <div class="fr-card__end">
                            <div class="fr-btns-group fr-btns-group--sm fr-btns-group--right fr-btns-group--inline-lg fr-btns-group--icon-left fr-mb-n4v">
                                <button
                                    class="fr-btn fr-btn--secondary fr-icon-edit-line modify-button"
                                    type="button"
                                    data-action="${this.identifier}#onModify:prevent:default"
                                    data-testid="lieu-edit-btn"
                                >
                                    Modifier
                                </button>
                                <button
                                    class="fr-btn fr-btn--secondary fr-icon-delete-bin-line delete-button"
                                    type="button"
                                    data-action="${this.identifier}#onDelete:prevent:default"
                                    data-testid="lieu-delete-btn"
                                >
                                    Supprimer
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </section>`
    }
}

applicationReady.then(app => {
    app.register("address-search-autocomplete", AddressSearchAutocompleteController)
    app.register("lieu-formset", BaseFormSetController)
    app.register("lieu-form", LieuFormController)
})

export {lieuxStore, prelevementsStore}
