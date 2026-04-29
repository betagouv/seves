import {applicationReady} from "Application"
import {BaseFormInModal} from "BaseFormInModal"
import {BaseFormSetController} from "BaseFormset"
import {collectFormValues} from "Forms"
import {uniqueId} from "Utils"

/**
 * @typedef ElementInfesteData
 * @property {string} type
 * @property {string} quantite_unite
 * @property {string} quantite
 * @property {string} espece
 * @property {string} especeLabel
 * @property {string} comments
 */

/**
 * ******** Targets ********
 * @property {HTMLSelectElement} especeFieldTarget
 * @property {HTMLInputElement} quantiteInputTarget
 * @property {HTMLInputElement[]} quantiteUniteInputTargets
 * @property {HTMLSelectElement[]} errorMessageTargets
 * ******** Values ********
 * @property {boolean} isValidValue
 */
class ElementInfesteFormController extends BaseFormInModal {
    static targets = ["especeField", "errorMessage", "quantiteInput", "quantiteUniteInput"]
    static values = {isValid: {type: Boolean, default: true}}

    connect() {
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

    initCard(elementInfeste) {
        this.shouldImmediatelyShowValue = false
        this.cardContainerTargets.forEach(it => it.remove())
        this.element.insertAdjacentHTML("beforeend", this.renderCard(elementInfeste))
        this.element.insertAdjacentHTML("beforeend", this.renderDeleteConfirmationDialog(elementInfeste))
        dsfr(this.dialogTarget).modal.conceal()
    }

    /**@param {ElementInfesteData} formValues */
    clean(formValues) {
        if (formValues.quantite_unite !== "" && formValues.quantite === "") {
            this.quantiteInputTarget.setCustomValidity(
                `Le champ « ${this.quantiteUniteInputTargets[0].labels[0].innerText} » est rempli. `
                    + "Veuillez renseigner une valeur ici.",
            )
            return this.quantiteInputTarget.reportValidity()
        }
        if (formValues.quantite !== "" && formValues.quantite_unite === "") {
            const first = this.quantiteUniteInputTargets[0]
            first.setCustomValidity(
                `Le champ « ${this.quantiteInputTarget.labels[0].innerText} » est rempli. `
                    + "Veuillez renseigner une valeur ici.",
            )
            return first.reportValidity()
        }
        return true
    }

    /**
     * @param {ElementInfesteData} _data
     * @return {string}
     */
    getDeleteConfirmationSentence(_data) {
        return "Souhaitez-vous réellement supprimer l'élément infesté ?"
    }

    /**
     * @param {ElementInfesteData} _data
     * @return {string}
     */
    getDeleteConfirmationTitle(_data) {
        return "Suppression d'un élément infesté"
    }

    onCloseForm() {
        // this.shouldImmediatelyShowValue indicates that the card has not be rendered yet.
        // In this case, the form is not considered valid and it should be deleted on close
        if (this.shouldImmediatelyShowValue) this.forceDelete()
        this.errorMessageTargets.forEach(it => it.remove())
    }

    /**
     * @param {ElementInfesteData} elementInfeste
     * @return {string}
     */
    renderCard(elementInfeste) {
        const id = uniqueId("element-infeste-card")
        const invalidWarning = this.isValidValue
            ? ""
            : `<div id="${id}--error-desc" class="fr-alert fr-alert--error fr-mb-2v" aria-live="polite" data-${this.identifier}-target="errorMessage">
                    <p>Ce formulaire contient des erreurs. Veuillez l'éditer pour les corriger</p>
                </div>`
        // language=HTML
        return `
            <section data-${this.identifier}-target="cardContainer">
                ${invalidWarning}
                <div class="fr-card" ${this.isValidValue ? "" : ` aria-labelledby="${id}--error-desc"`} data-testid="element-card">
                    <div class="fr-card__body">
                        <div class="fr-card__content">
                            <h3
                                class="fr-card__title"
                                data-${this.identifier}-target="denomination"
                                aria-labelledby="${id}--button"
                            >
                                <button
                                    id="${id}--button"
                                    class="fr-link"
                                    type="button"
                                    data-action="${this.identifier}#onModify:prevent:default"
                                >
                                    ${elementInfeste.type}
                                </button>
                            </h3>
                            <div class="fr-card__desc fr-mt-4v fr-flex fr-flex--gap-2v">
                                ${this.optionalText(
                                    elementInfeste.especeLabel,
                                    `<p class="fr-mb-0">Espèce végétale : ${elementInfeste.especeLabel}</p>`,
                                )}
                                ${this.optionalText(
                                    elementInfeste.quantite,
                                    `<p class="fr-mb-0">Quantité d’éléments infestés : ${elementInfeste.quantite} ${elementInfeste.quantite_unite}</p>`,
                                )}

                                <div class="fr-btns-group fr-btns-group--inline-lg fr-btns-group--icon-left fr-btns-group--sm fr-btns-group--right fr-mt-4v fr-mb-n4v">
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
}

applicationReady.then(app => {
    app.register("element-infeste-formset", BaseFormSetController)
    app.register("element-infeste-form", ElementInfesteFormController)
})
