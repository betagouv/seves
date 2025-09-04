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
 * @property {String} communesApiValue
 * @property {String} emptyFormPrefixValue
 * @property {Boolean} renderInitialValue
 */
class EtablissementFormController  extends Controller {
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
    ]
    static values = {communesApi: String, emptyFormPrefix: String, renderInitial: Boolean}

    connect() {
        this.raisonSocialeInputTarget.required = true
        this.addressChoices = setUpAddressChoices(this.adresseInputTarget)
        setUpSiretChoices(this.siretInputTarget, "bottom")
        this.initCard()
    }

    onAddressChoice(event){
        this.communeInputTarget.value = event.detail.customProperties.city
        this.codeInseeInputTarget.value = event.detail.customProperties.inseeCode
        if (!!event.detail.customProperties.context)
        {
            this.paysInputTarget.value = "FR"
            const [num, ..._] = event.detail.customProperties.context.split(/\s*,\s*/)
            this.departementInputTarget.value = num
        }
    }

    onSiretChoice({detail: {customProperties: {code_commune,commune, raison, siret, streetData}}}) {
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
            }).catch(() => {/* NOOP */})
        }
    }

    openDialog() {
        requestAnimationFrame(() => {
            dsfr(this.dialogTarget).modal.disclose()
        })
    }

    closeDialog() {
        requestAnimationFrame(() => {
            dsfr(this.dialogTarget).modal.conceal()
        })
    }

    onValidateForm(){
        if(this.fieldsetTarget.checkValidity()) {
            this.initCard()
        }
    }

    onModify() {
        this.openDialog()
    }

    onDisplay() {
    }

    onDelete() {
    }

    onDeleteConfirm() {
        this.deleteInputTarget.value = "on"
        this.cardContainerTarget.remove()
        this.closeDialog()
    }

    initCard() {
        let hasData = false
        const etablissement = {}

        for (const input of this.fieldsetTarget.elements) {
            if(typeof input.value === "string" && input.value.length > 0) {
                hasData = true
            }
            etablissement[input.name.replace(`${this.emptyFormPrefixValue}-`, "")] = input.value
        }

        if(!hasData) { // Case of an empty new form
            this.openDialog()
            return
        }

        this.cardContainerTargets.forEach(it => it.remove())
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
                            class="fr-btn fr-icon-search-line fr-mb-0"
                            type="button"
                            data-action="${this.identifier}#onDisplay:prevent:default"
                        >
                            Voir les informations de l'établissement ${etablissement.raison_sociale}
                        </button>
                        <button
                            class="fr-btn fr-btn--secondary fr-icon-edit-line fr-mb-0"
                            type="button"
                            data-action="${this.identifier}#onModify:prevent:default"
                        >Modifier l'établissement ${etablissement.raison_sociale}</button>
                        <button
                            class="fr-btn fr-btn--secondary fr-icon-delete-bin-line fr-mb-0"
                            type="button"
                            data-action="${this.identifier}#onDelete:prevent:default"
                        >Supprimer l'établissement ${etablissement.raison_sociale}</button>
                    </div>
                </div>
            </div>
        </div>`
    }
}

applicationReady.then(app => {
    app.register("etablissement-formset", BaseFormSetController)
    app.register("etablissement-form", EtablissementFormController)
})
