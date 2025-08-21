import {AbstractFormSetController} from "BaseFormset"
import {applicationReady} from "Application";
import {formIsValid, removeRequired, getSelectedLabel} from "/static/core/forms.mjs";
import {setUpAddressChoices} from "/static/core/ban_autocomplete.js";

import "dsfr";

class EtablissementsFormSetController extends AbstractFormSetController {
    static targets = [...this.targets, "cardTemplate", "cardContainer", "raisonSociale"]

    onAddForm(){
        const html = this.emptyFormTplTarget.innerHTML.replace(/__prefix__/g, `${this.TOTAL_FORMSValue}`)
        this.formsetContainerTarget.insertAdjacentHTML("beforeend", html)
        const currentModal = document.querySelector(`#fr-modal-etablissement${this.TOTAL_FORMSValue}`)
        this.TOTAL_FORMSValue += 1
        currentModal.querySelector('[id$=raison_sociale]').required = true
        this._setupAdresseField(currentModal)
        requestAnimationFrame(() => {
            dsfr(currentModal).modal.disclose()
        })
    }

    _setupAdresseField(modal){
        const addressChoices = setUpAddressChoices(modal.querySelector('[id$=adresse_lieu_dit]'))
        addressChoices.passedElement.element.addEventListener("choice", (event)=> {
            modal.querySelector('[id$=commune]').value = event.detail.customProperties.city
            modal.querySelector('[id$=code_insee]').value = event.detail.customProperties.inseeCode
            if (!!event.detail.customProperties.context)
            {
                modal.querySelector('[id$=pays]').value = "FR"
                const [num, ...rest] = event.detail.customProperties.context.split(/\s*,\s*/)
                modal.querySelector('[id$=departement]').value = num
            }
        })
        return addressChoices
    }

    _getEtablissementCard(baseCard, currentModal){
        baseCard.querySelector('.raison-sociale').textContent = currentModal.querySelector('[id$=raison_sociale]').value

        const siret = currentModal.querySelector('[id$=siret]').value
        if (siret != "") {
            baseCard.querySelector('.siret').innerText = siret
            baseCard.querySelector('.siret').classList.remove("fr-hidden")
        }

        const commune = currentModal.querySelector('[id$=commune]').value
        const departementLabel = getSelectedLabel(currentModal.querySelector('[id$=departement]'))
        if(commune != "" || departementLabel != null){
            const adresse = [
                commune,
                departementLabel ? `| ${departementLabel}` : null
            ].filter(Boolean).join(" ");

            baseCard.querySelector('.adresse').innerText = adresse
            baseCard.querySelector('.adresse').classList.remove("fr-hidden")
        }

        const type = currentModal.querySelector('[id$=type_etablissement]').value
        if (type != "") {
            baseCard.querySelector('.type').innerText = type
            baseCard.querySelector('.type').classList.remove("fr-hidden")
        }
        return baseCard
    }

    _getAndAddCardToList(currentModal){
        const clone = this.cardTemplateTarget.content.cloneNode(true);
        const card = this._getEtablissementCard(clone, currentModal)
        this.cardContainerTarget.appendChild(card)
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

applicationReady.then(app => {
    app.register("etablissement-formset", EtablissementsFormSetController)
})
