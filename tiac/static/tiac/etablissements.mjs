import {AbstractFormSetController} from "BaseFormset"
import {applicationReady} from "Application";
import {formIsValid, removeRequired, getSelectedLabel} from "Forms";
import {setUpAddressChoices} from "BanAutocomplete";
import {Controller} from "Stimulus";
import {useStore, createStore} from "StimulusStore"

const cardsStore = createStore({
    name: "cards",
    type: Array,
    initialValue: [],
});


class EtablissementFormController  extends Controller {
    static stores = [cardsStore]
    static targets = ["cardTemplate", "raisonSocialeInput", "communeInput", "departementInput", "paysInput", "adresseInput", "typeEtablissementInput", "codeInseeInput"]

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

    connect() {
        useStore(this)
        this.raisonSocialeInputTarget.required = true
        setUpAddressChoices(this.adresseInputTarget)
        requestAnimationFrame(() => {
            dsfr(this.element).modal.disclose()
        })
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
