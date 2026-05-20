import {applicationReady, escapeHTML} from "Application"
import {BaseFormInModal} from "BaseFormInModal"
import {BaseFormSetController} from "BaseFormset"
import {collectFormValues} from "Forms"
import {createStore, useStore} from "StimulusStore"

/**
 * @typedef LiueData
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

/**
 * ******** Targets ********
 * @property {HTMLSelectElement} addressTarget
 * @property {HTMLSelectElement} communeTarget
 * @property {HTMLInputElement} codeInseeTarget
 * @property {HTMLInputElement} codePostalTarget
 * @property {HTMLSelectElement} departementTarget
 * @property {HTMLInputElement} latitudeTarget
 * @property {HTMLInputElement} longitudeTarget
 * @property {HTMLElement[]} errorMessageTargets
 * ******** Values ********
 * @property {boolean} isValidValue
 * ******** Outlets ********
 * @property {CommuneSearchController} communesSearchOutlet
 * ******** Stores ********
 * @property  {function(value: import("StimulusStore/dist/types/setCallback").SetCallback)}  setLieuxStoreValue
 * @property  {import("StimulusStore/dist/types/updateMethod").UpdateMethod}  onLieuxStoreUpdate
 * @property {Object} lieuxStoreValue
 */
class LieuFormController extends BaseFormInModal {
    static targets = [
        "errorMessage",
        "address",
        "commune",
        "codeInsee",
        "codePostal",
        "departement",
        "latitude",
        "longitude",
        "etablissementAddress",
    ]
    static values = {isValid: {type: Boolean, default: true}}
    static outlets = ["communes-search"]
    static stores = [lieuxStore]

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

    /** @param {LiueData} lieu */
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

    /**
     * @param {ElementInfesteData} _data
     * @return {string}
     */
    getDeleteConfirmationSentence(_data) {
        return "Souhaitez-vous réellement supprimer le lieu ?"
    }

    /**
     * @param {ElementInfesteData} _data
     * @return {string}
     */
    getDeleteConfirmationTitle(_data) {
        return "Suppression d'un lieu"
    }

    onCloseForm() {
        // this.shouldImmediatelyShowValue indicates that the card has not be rendered yet.
        // In this case, the form is not considered valid and it should be deleted on close
        if (this.shouldImmediatelyShowValue) this.forceDelete()
        this.errorMessageTargets.forEach(it => it.remove())
    }

    onCommuneChoice({detail: {value, customProperties}}) {
        this.#updateFields([
            [this.communeTarget, value],
            [this.codeInseeTarget, customProperties.inseeCode],
            [this.codePostalTarget, customProperties.postCode],
            [this.departementTarget, customProperties.departementCode],
        ])
    }

    onCommuneRemoveItem() {
        this.communesSearchOutlet.setValue()
    }

    onCommuneForcedChoice({detail: {value}}) {
        this.communesSearchOutlet.setValue([value])
    }

    onAddressChoice({detail: {customProperties}}) {
        const departementCode = (customProperties.context || "").split(",")[0].trim()
        this.communesSearchOutlet.setValue([customProperties.city])
        this.#updateFields([
            [this.departementTarget, departementCode],
            [this.communeTarget, customProperties.city],
            [this.codeInseeTarget, customProperties.inseeCode],
            [this.codePostalTarget, customProperties.postCode],
            [this.latitudeTarget, customProperties.lat],
            [this.longitudeTarget, customProperties.long],
        ])
    }

    onAddressRemoveItem() {}

    onAddressForcedChoice({detail: {value}}) {
        this.communesSearchOutlet.setValue([value])
    }

    /**
     * @param {LiueData} lieu
     * @return {string}
     */
    renderCard(lieu) {
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
        return `<section id="${this.formPrefixValue}--card" data-${this.identifier}-target="cardContainer">
            ${this.optionalText(
                this.isValidValue,
                `<div id="${this.formPrefixValue}--error-desc" class="fr-alert fr-alert--error fr-mb-2v" aria-live="polite" data-${this.identifier}-target="errorMessage">
                    <p>Ce formulaire contient des erreurs. Veuillez l'éditer pour les corriger</p>
                </div>`,
            )}
            <div class="fr-card seves-card"${this.optionalText(this.isValidValue, ` aria-labelledby="${this.formPrefixValue}--error-desc"`)} data-testid="element-card">
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
                                >Modifier
                                </button>
                                <button
                                    class="fr-btn fr-btn--secondary fr-icon-delete-bin-line delete-button"
                                    type="button"
                                    data-action="${this.identifier}#onDelete:prevent:default"
                                >Supprimer
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </section>`
    }

    /** @param {[HTMLElement, any][]} fieldsAndValues */
    #updateFields(fieldsAndValues) {
        for (const [it, value] of fieldsAndValues) {
            it.value = value
            if (it instanceof HTMLInputElement) {
                it.dispatchEvent(new Event("input"))
            } else {
                it.dispatchEvent(new Event("change"))
            }
        }
    }
}

applicationReady.then(app => {
    app.register("lieu-formset", BaseFormSetController)
    app.register("lieu-form", LieuFormController)
    document.lieuxCards = {}
})

export {lieuxStore}
