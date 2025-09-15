import {BaseFormSetController} from "BaseFormset"
import {applicationReady} from "Application";
import {setUpAddressChoices} from "BanAutocomplete"
import {Controller} from "Stimulus";
import {setUpSiretChoices} from "siret"

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
 * @property {String} communesApiValue
 * @property {String} formPrefixValue
 */
class EtablissementFormController extends Controller {
    static targets = [
        "raisonSocialeInput",
        "communeInput",
        "departementInput",
        "paysInput",
        "adresseInput",
        "typeEtablissementInput",
        "codeInseeInput",
        "siretInput",
        "deleteInput",
        "fieldset",
        "dialog",
        "cardContainer",
        "deleteModal",
        "detailModalContainer",
        "detailModal",
    ]
    static values = {communesApi: String, formPrefix: String}

    connect() {
        this.raisonSocialeInputTarget.required = true
        this.addressChoices = setUpAddressChoices(this.adresseInputTarget)
        setUpSiretChoices(this.siretInputTarget, "bottom")
        this.initCard()
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

    openForm() {
        dsfr(this.dialogTarget).modal.disclose()
    }

    closeForm() {
        dsfr(this.dialogTarget).modal.conceal()
    }

    onCloseForm() {
        const [hasData, ..._] = this.computeData()
        if (!hasData) this.forceDelete()
    }

    onValidateForm() {
        for (const element of this.fieldsetTarget.elements) {
            if(!element.checkValidity()) {
                if(element.dataset.message) {
                    element.setCustomValidity(element.dataset.message)
                }
                element.reportValidity()
                return
            }
        }
        this.initCard()
    }

    onModify() {
        this.openForm()
    }

    onDetailDisplay() {
        dsfr(this.detailModalTarget).modal.disclose()
    }

    onCancelDelete() {
        dsfr(this.deleteModalTarget).modal.conceal()
    }

    onDelete() {
        dsfr(this.deleteModalTarget).modal.disclose()
    }

    onDeleteConfirm() {
        this.forceDelete()
        dsfr(this.deleteModalTarget).modal.conceal()
    }

    forceDelete() {
        this.deleteInputTarget.value = "on"
        this.fieldsetTarget.setAttribute("disabled", "disabled")
        this.element.classList.add("fr-hidden")
    }

    computeData() {
        let hasData = false
        const etablissement = {}

        for (const input of this.fieldsetTarget.elements) {
            if (!input.name || input.name.length === 0) continue;

            const inputName = input.name.replace(`${this.formPrefixValue}-`, "")
            const inputValue = typeof input.value === "string" ? input.value.trim() : ""

            if (inputValue !== "") {
                hasData = true
            }

            if (input instanceof HTMLSelectElement && input.dataset.choice === undefined && inputValue !== "") {
                const option = input.options[input.selectedIndex]
                etablissement[inputName] = option ? option.innerText.trim() : ""
            } else {
                etablissement[inputName] = input.value
            }
        }

        return [hasData, etablissement]
    }

    initCard() {
        const [hasData, etablissement] = this.computeData()
        if (!hasData) { // Case of an empty new form
            this.openForm()
            return
        }

        this.cardContainerTargets.forEach(it => it.remove())
        this.detailModalContainerTargets.forEach(it => it.remove())
        this.element.insertAdjacentHTML("beforeend", this.renderCardDetailModal(etablissement))
        this.element.insertAdjacentHTML("beforeend", this.renderDeleteConfirmationDialog(etablissement))
        this.element.insertAdjacentHTML("beforeend", this.renderCard(etablissement))
        dsfr(this.dialogTarget).modal.conceal()
    }

    /**
     * @param {EtablissementData} etablissement
     * @return {string} HTML
     */
    renderCard(etablissement) {
        function optional(value, text) {
            return value ? (text || `${value}`) : ""
        }

        function join(delimiter, ...items) {
            return items.filter(it => !!it.length).join(delimiter)
        }

        // languague=HTML
        return `<div class="etablissement-card fr-card" data-${this.identifier}-target="cardContainer">
            <div class="fr-card__body">
                <div class="fr-card__content">
                    <h3 class="fr-card__title raison-sociale" data-${this.identifier}-target="raisonSociale">
                      ${etablissement.raison_sociale}
                    </h3>
                    <div class="fr-card__desc">
                        <address class="fr-card__detail fr-icon-map-pin-2-line fr-my-2v adresse">
                            ${join(" | ", etablissement.departement, etablissement.commune)}
                        </address>
                        ${optional(etablissement.siret, `<p>Siret : ${etablissement.siret}</p>`)}
                        ${optional(
            etablissement.type_etablissement,
            `<p class="fr-badge fr-badge--info">${etablissement.type_etablissement}</p>`
        )}
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

    /**
     * @param {EtablissementData} etablissement
     * @return {string} HTML
     */
    renderDeleteConfirmationDialog(etablissement) {
        // languague=HTML
        return `<button class="fr-btn fr-hidden" data-fr-opened="false" aria-controls="${this.formPrefixValue}-delete-modal"></button>
            <dialog
                id="${this.formPrefixValue}-delete-modal"
                class="fr-modal delete-modal"
                aria-labelledby="delete-modal-title"
                aria-modal="true"
                data-${this.identifier}-target="deleteModal"
            >
                <div class="fr-container fr-container--fluid">
                    <div class="fr-grid-row fr-grid-row--center">
                        <div class="fr-col-12 fr-col-md-8 fr-col-lg-6">
                            <div class="fr-modal__body">
                                <div class="fr-modal__content">
                                    <h3 id="delete-modal-title" class="fr-modal__title">
                                        <span class="fr-icon-arrow-right-line fr-icon--lg" aria-hidden="true"></span>
                                        Suppression d'un établisssment
                                    </h3>
                                    <p>Confimez-vous vouloir supprimer l'établissement ${etablissement.raison_sociale}</p>
                                </div>
                                <div class="fr-modal__footer">
                                    <div class="fr-btns-group fr-btns-group--right fr-btns-group--inline-lg">
                                        <button
                                            class="fr-btn fr-btn--secondary delete-cancel"
                                            data-action="${this.identifier}#onCancelDelete:prevent:default"
                                        >Annuler</button>
                                        <button
                                            class="fr-btn delete-confirmation"
                                            data-action="${this.identifier}#onDeleteConfirm:prevent:default"
                                        >Supprimer</button>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </dialog>`
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
