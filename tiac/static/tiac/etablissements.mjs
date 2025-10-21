import {BaseFormSetController} from "BaseFormset"
import {applicationReady} from "Application";
import {setUpAddressChoices} from "BanAutocomplete"
import {setUpSiretChoices} from "siret"
import {collectFormValues} from "Forms"
import {BaseFormInModal} from "BaseFormInModal"

/**
 * @typedef EtablissementData
 * @property {String} adresse_lieu_dit
 * @property {String} code_insee
 * @property {String} commune
 * @property {String} departement
 * @property {String} pays
 * @property {String} raison_sociale
 * @property {String} siret
 * @property {String} type_etablissement
 * @property {String} numero_resytal
 * @property {String} date_inspection
 * @property {String} evaluation
 * @property {String} commentaire
 */

/**
 * @property {HTMLInputElement} raisonSocialeInputTarget
 * @property {HTMLInputElement} adresseInputTarget
 * @property {HTMLSelectElement} departementInputTarget
 * @property {HTMLInputElement} paysInputTarget
 * @property {HTMLInputElement} codeInseeInputTarget
 * @property {HTMLInputElement} communeInputTarget
 * @property {HTMLInputElement} siretInputTarget
 * @property {HTMLInputElement} deleteInputTarget
 * @property {HTMLElement} cardContainerTarget
 * @property {HTMLFormElement} fieldsetTarget
 * @property {HTMLDialogElement} dialogTarget
 * @property {HTMLElement[]} cardContainerTargets
 * @property {HTMLDialogElement} deleteModalTarget
 * @property {HTMLDialogElement} detailModalTarget
 * @property {HTMLInputElement} hasInspectionTarget
 * @property {HTMLElement} inspectionFieldsTarget
 * @property {String} communesApiValue
 * @property {String} formPrefixValue
 * @property {Boolean} shouldImmediatelyShowValue
 */
class EtablissementFormController extends BaseFormInModal {
    static targets = [
        "raisonSocialeInput",
        "communeInput",
        "departementInput",
        "paysInput",
        "adresseInput",
        "typeEtablissementInput",
        "codeInseeInput",
        "siretInput",
        "detailModal",
        "hasInspection",
        "inspectionFields",
    ]
    static values = {communesApi: String, shouldImmediatelyShow: {type: Boolean, default: false}}

    connect() {
        this.raisonSocialeInputTarget.required = true
        this.addressChoices = setUpAddressChoices(this.adresseInputTarget)
        setUpSiretChoices(this.siretInputTarget, "bottom")
        if (this.shouldImmediatelyShowValue) {
            this.openDialog()
        } else {
            this.initCard(
                collectFormValues(this.fieldsetTarget, {
                    nameTransform: name => name.replace(`${this.formPrefixValue}-`, ""),
                    skipValidation: true
                })
            )
        }
        // Forces the has_inspection toggle to deliver an initial value
        this.hasInspectionTarget.dispatchEvent(new Event("input"))
    }

    onAddressChoice(event) {
        this.communeInputTarget.value = event.detail.customProperties.city
        this.codeInseeInputTarget.value = event.detail.customProperties.inseeCode
        if (!!event.detail.customProperties.context) {
            this.paysInputTarget.value = "FR"
            const [num, ..._] = event.detail.customProperties.context.split(/\s*,\s*/)
            this.departementInputTarget.value = num
        }
    }

    onSiretChoice({detail: {customProperties: {code_commune, commune, raison, siret, streetData}}}) {
        this.siretInputTarget.value = siret
        this.raisonSocialeInputTarget.value = raison
        this.communeInputTarget.value = commune
        this.codeInseeInputTarget.value = code_commune
        this.paysInputTarget.value = "FR"

        if (!!streetData) {
            let result = [
                {
                    "value": streetData,
                    "label": streetData,
                    selected: true
                }
            ]
            this.addressChoices.setChoices(result, 'value', 'label', true)

        }

        if (!!code_commune && !!this.communesApiValue) {
            fetch(`${this.communesApiValue}/${code_commune}?fields=departement`).then(async response => {
                const json = await response.json()
                this.departementInputTarget.value = json.departement.code
            }).catch(() => {/* NOOP */
            })
        }
    }

    onCloseForm() {
        // this.shouldImmediatelyShowValue indicates that the card has not be rendered yet.
        // In this case, the form is not considered valid and it should be deleted on close
        if (this.shouldImmediatelyShowValue) this.forceDelete()
    }

    onInspectionToggle({target: {checked}}) {
        if (checked) {
            this.inspectionFieldsTarget.classList.remove("fr-hidden")
        } else {
            this.inspectionFieldsTarget.classList.add("fr-hidden")
        }
    }

    /** @param {EtablissementData} etablissement */
    initCard(etablissement) {
        this.shouldImmediatelyShowValue = false;
        this.cardContainerTargets.forEach(it => it.remove())
        this.element.insertAdjacentHTML("beforeend", this.renderDeleteConfirmationDialog(etablissement))
        this.element.insertAdjacentHTML("beforeend", this.renderCard(etablissement))
        requestAnimationFrame(() => dsfr(this.dialogTarget).modal.conceal())
    }

    /**
     * @param {EtablissementData} etablissement
     * @return {string} HTML
     */
    renderCard(etablissement) {
        // language=HTML
        return `<div class="etablissement-card fr-card" data-${this.identifier}-target="cardContainer">
            <div class="fr-card__body">
                <div class="fr-card__content">
                    <h3 class="fr-card__title raison-sociale" data-${this.identifier}-target="raisonSociale">
                      ${etablissement.raison_sociale}
                    </h3>
                    <div class="fr-card__desc">
                        <address class="fr-card__detail fr-icon-map-pin-2-line fr-my-2v adresse">
                            ${this.joinText(" | ", etablissement.commune, etablissement.departement)}
                        </address>
                        ${this.optionalText(etablissement.siret, `<p>Siret : ${etablissement.siret}</p>`)}
                        ${this.optionalText(etablissement.type_etablissement, this.renderBadges([etablissement.type_etablissement]))}
                    </div>
                </div>
                <div class="fr-card__footer">
                    <div class="fr-btns-group fr-btns-group--inline-lg fr-btns-group--icon-left fr-btns-group--sm fr-btns-group--right">
                        <button
                            class="fr-btn fr-btn--secondary fr-icon-edit-line modify-button"
                            type="button"
                            title="Modifier l'établissement ${etablissement.raison_sociale}"
                            data-action="${this.identifier}#onModify:prevent:default"
                        >Modifier</button>
                        <button
                            class="fr-btn fr-btn--secondary fr-icon-delete-bin-line delete-button"
                            type="button"
                            title="Supprimer l'établissement ${etablissement.raison_sociale}"
                            data-action="${this.identifier}#onDelete:prevent:default"
                        >Supprimer</button>
                    </div>
                </div>
            </div>
        </div>`
    }

    getDeleteConfirmationSentence(etablissement){
        return `Confimez-vous vouloir supprimer l'établissement ${etablissement.raison_sociale} ?`
    }

    getDeleteConfirmationTitle(etablissement){
        return "Suppression d'un établissement"
    }
}

applicationReady.then(app => {
    app.register("etablissement-formset", BaseFormSetController)
    app.register("etablissement-form", EtablissementFormController)
})
