import {AbstractFormSetController} from "BaseFormset"
import {applicationReady} from "Application";
import {formIsValid, removeRequired, getSelectedLabel} from "Forms";
import {setUpAddressChoices} from "BanAutocomplete";
import {Controller} from "Stimulus";
import {useStore, createStore} from "StimulusStore"
import {setUpSiretChoices} from "siret"

const cardsStore = createStore({
    name: "cards",
    type: Array,
    initialValue: [],
});

/**
 * @property {HTMLInputElement} raisonSocialeInputTarget
 * @property {HTMLInputElement} adresseInputTarget
 * @property {HTMLInputElement} departementInputTarget
 * @property {HTMLInputElement} paysInputTarget
 * @property {HTMLInputElement} codeInseeInputTarget
 * @property {HTMLInputElement} communeInputTarget
 * @property {HTMLInputElement} siretInputTarget
 * @property {String} communesApiValue
 */
class EtablissementFormController  extends Controller {
    static stores = [cardsStore]
    static targets = [
        "cardTemplate",
        "raisonSocialeInput",
        "communeInput",
        "departementInput",
        "paysInput",
        "adresseInput",
        "typeEtablissementInput",
        "codeInseeInput",
        "siretInput",
    ]
    static values = {communesApi: String}

    connect() {
        useStore(this)
        this.raisonSocialeInputTarget.required = true
        this.addressChoices = setUpAddressChoices(this.adresseInputTarget)
        setUpSiretChoices(this.siretInputTarget, "bottom")
        requestAnimationFrame(() => {
            dsfr(this.element).modal.disclose()
        })
    }

    onAddressChoice(event){
        this.communeInputTarget.value = event.detail.customProperties.city
        this.codeInseeInputTarget.value = event.detail.customProperties.inseeCode
        if (!!event.detail.customProperties.context)
        {
            this.paysInputTarget.value = "FR"
            const [num, ...rest] = event.detail.customProperties.context.split(/\s*,\s*/)
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
                const json = await response.json();
                this.departementInputTarget.value = json.departement.code;
            })
        }
    }

    _getEtablissementCard(baseCard, currentModal){
        baseCard.querySelector('.raison-sociale').textContent = this.raisonSocialeInputTarget.value

        const commune = this.communeInputTarget.value
        const departementLabel = getSelectedLabel(this.departementInputTarget)
        if(commune != "" || departementLabel != null){
            const adresse = [
                commune,
                departementLabel ? `| ${departementLabel}` : null
            ].filter(Boolean).join(" ");

            baseCard.querySelector('.adresse').innerText = adresse
            baseCard.querySelector('.adresse').classList.remove("fr-hidden")
        }

        const type = this.typeEtablissementInputTarget.value
        if (type != "") {
            baseCard.querySelector('.type').innerText = type
            baseCard.querySelector('.type').classList.remove("fr-hidden")
        }
        return baseCard
    }

    _getAndAddCardToList(currentModal){
        const clone = this.cardTemplateTarget.content.cloneNode(true);
        const card = this._getEtablissementCard(clone, currentModal)
        this.setCardsValue([...this.cardsValue, card])
    }

    validateForm(event){
        const currentModal = event.target.closest("dialog")
        if (formIsValid(currentModal) === false) {
            return
        }

        this._getAndAddCardToList(currentModal)
        dsfr(currentModal).modal.conceal()
        removeRequired(currentModal)
    }
}

class EtablissementsFormSetController extends AbstractFormSetController {
    static targets = [...AbstractFormSetController.targets, "cardContainer"]
    static stores = [cardsStore]

    connect() {
        useStore(this)
        this._initializeFieldValues()
    }

    onCardsUpdate(cardsValue) {
        this.cardContainerTarget.innerHTML = ""
        cardsValue.forEach(fragment => {
            this.cardContainerTarget.appendChild(fragment.cloneNode(true))
        })
    }
}

applicationReady.then(app => {
    app.register("etablissement-formset", EtablissementsFormSetController)
    app.register("etablissement-form", EtablissementFormController)
})
