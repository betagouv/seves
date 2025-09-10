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
 * @property {HTMLElement[]} detailModalContainerTargets
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
        "detailModalContainer",
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

    onDetailDisplay() {
        dsfr(this.detailModalTarget).modal.disclose()
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
        this.detailModalContainerTargets.forEach(it => it.remove())
        this.element.insertAdjacentHTML("beforeend", this.renderCardDetailModal(etablissement))
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
                            ${this.joinText(" | ", etablissement.departement, etablissement.commune)}
                        </address>
                        ${this.optionalText(etablissement.siret, `<p>Siret : ${etablissement.siret}</p>`)}
                        ${this.optionalText(etablissement.type_etablissement, `<p class="fr-badge fr-badge--info">${etablissement.type_etablissement}</p>`)}
                    </div>
                </div>
                <div class="fr-card__footer">
                    <div class="fr-btns-group fr-btns-group--inline fr-btns-group--sm fr-btns-group--right">
                        <button
                            class="fr-btn fr-icon-search-line fr-mb-0 detail-display"
                            type="button"
                            data-action="${this.identifier}#onDetailDisplay:prevent:default"
                        >
                            Voir les informations de l'établissement ${etablissement.raison_sociale}
                        </button>
                        <button
                            class="fr-btn fr-btn--secondary fr-icon-edit-line fr-mb-0 modify-button"
                            type="button"
                            data-action="${this.identifier}#onModify:prevent:default"
                        >Modifier l'établissement ${etablissement.raison_sociale}</button>
                        <button
                            class="fr-btn fr-btn--secondary fr-icon-delete-bin-line fr-mb-0 delete-button"
                            type="button"
                            data-action="${this.identifier}#onDelete:prevent:default"
                        >Supprimer l'établissement ${etablissement.raison_sociale}</button>
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


    /**
     * @param {EtablissementData} etablissement
     * @return {string} HTML
     */
    renderCardDetailModal(etablissement) {
        // languague=HTML
        return `<div data-${this.identifier}-target="detailModalContainer">
            <button class="fr-btn fr-hidden" data-fr-opened="false" aria-controls="${this.formPrefixValue}-detail-modal"></button>
            <dialog
                id="${this.formPrefixValue}-detail-modal"
                class="fr-modal detail-modal"
                aria-labelledby="detail-modal-title"
                aria-modal="true"
                data-${this.identifier}-target="detailModal"
            >
                <div class="fr-container fr-container--fluid">
                    <div class="fr-grid-row">
                        <div class="fr-col">
                            <div class="fr-modal__body">
                                <div class="fr-modal__header">
                                <button
                                    class="fr-btn--close fr-btn"
                                    title="Fermer" aria-controls="${this.formPrefixValue}-detail-modal"
                                    type="button"
                                >Fermer</button>
                                </div>
                                <div class="fr-modal__content">
                                    <h3 id="detail-modal-title" class="fr-modal__title">
                                        <span class="fr-icon-arrow-right-line fr-icon--lg" aria-hidden="true"></span>
                                        ${etablissement.raison_sociale}
                                    </h3>
                                    <div class="fr-grid-row fr-grid-row--gutters fr-grid-row--border">
                                        <div class="fr-col fr-col-md-6">
                                            <div class="fr-grid-row">
                                                <p class="fr-col fr-col-md-6 fr-text--bold">Type d'établissement</p>
                                                <p class="fr-col fr-col-md-6">
                                                    ${etablissement.type_etablissement ? `<span class="fr-badge fr-badge--info">${etablissement.type_etablissement}</span>` : ""}
                                                </p>
                                            </div>
                                            <div class="fr-grid-row">
                                                <p class="fr-col fr-col-md-6 fr-text--bold">SIRET</p>
                                                <p class="fr-col fr-col-md-6">${etablissement.siret}</p>
                                            </div>
                                            <div class="fr-grid-row">
                                                <p class="fr-col fr-col-md-6 fr-text--bold">Enseigne usuelle</p>
                                                <p class="fr-col fr-col-md-6">${etablissement.raison_sociale}</p>
                                            </div>
                                            <div class="fr-grid-row">
                                                <p class="fr-col fr-col-md-6 fr-text--bold">Adresse</p>
                                                <p class="fr-col fr-col-md-6">${etablissement.adresse_lieu_dit}</p>
                                            </div>
                                            <div class="fr-grid-row">
                                                <p class="fr-col fr-col-md-6 fr-text--bold">Commune</p>
                                                <p class="fr-col fr-col-md-6">${etablissement.commune}</p>
                                            </div>
                                            <div class="fr-grid-row">
                                                <p class="fr-col fr-col-md-6 fr-text--bold">Departement</p>
                                                <p class="fr-col fr-col-md-6">${etablissement.departement}</p>
                                            </div>
                                        </div>
                                        <div class="fr-col fr-col-md-6">
                                            <div class="fr-grid-row">
                                                <p class="fr-col fr-col-md-6 fr-text--bold">Numéro Resytal</p>
                                                <p class="fr-col fr-col-md-6">${etablissement.numero_resytal}</p>
                                            </div>
                                            <div class="fr-grid-row">
                                                <p class="fr-col fr-col-md-6 fr-text--bold">Date d'inspection</p>
                                                <p class="fr-col fr-col-md-6">${etablissement.date_inspection}</p>
                                            </div>
                                            <div class="fr-grid-row">
                                                <p class="fr-col fr-col-md-6 fr-text--bold">Évaluation globale</p>
                                                <p class="fr-col fr-col-md-6">${etablissement.evaluation}</p>
                                            </div>
                                            <div class="fr-grid-row">
                                                <p class="fr-col fr-col-md-6 fr-text--bold">Commentaire</p>
                                                <p class="fr-col fr-col-md-6">${etablissement.commentaire}</p>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </dialog>
        </div>`
    }
}

applicationReady.then(app => {
    app.register("etablissement-formset", BaseFormSetController)
    app.register("etablissement-form", EtablissementFormController)
})
