import {AbstractFormSetController} from "BaseFormset"
import {applicationReady} from "Application";
import "dsfr";

class EtablissementsFormSetController extends AbstractFormSetController {
    static targets = [...this.targets, "cardTemplate", "cardContainer"]

    onAddForm(){
        const html = this.emptyFormTplTarget.innerHTML.replace(/__prefix__/g, `${this.TOTAL_FORMSValue}`)
        this.formsetContainerTarget.insertAdjacentHTML("beforeend", html)
        const currentModal = document.querySelector(`#fr-modal-etablissement${this.TOTAL_FORMSValue}`)
        this.TOTAL_FORMSValue += 1
        currentModal.querySelector('[id$=raison_sociale]').required = true
        requestAnimationFrame(() => {
            dsfr(currentModal).modal.disclose()
        })
    }

    _getEtablissementCard(baseCard, currentModal){

        baseCard.querySelector('.raison-sociale').textContent = currentModal.querySelector('[id$=raison_sociale]').value
        // Addresse
        // Siret
        // Type etablissement

        return baseCard
    }

    _getAndAddCardToList(currentModal){
        const clone = this.cardTemplateTarget.content.cloneNode(true);
        const card = this._getEtablissementCard(clone, currentModal)
        this.cardContainerTarget.appendChild(card)
    }

    validateForm(event){
        const currentModal = event.target.closest("dialog")
        // TODO use a module for this ?
        // if (formIsValid(currentModal) === false) {
        //     return
        // }

        this._getAndAddCardToList(currentModal)
        dsfr(currentModal).modal.conceal()

        // TODO use a module for this ?
        // removeRequired(currentModal)
    }
}

applicationReady.then(app => {
    app.register("etablissement-formset", EtablissementsFormSetController)
})
