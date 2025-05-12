import {setUpAddressChoices} from "/static/core/ban_autocomplete.js";

let modalEtablissementHTMLContent = {}

document.addEventListener('DOMContentLoaded', () => {
    function getNextIdToUse() {
        let num = 0
        while (document.getElementById(`id_etablissements-${num}-raison_sociale`)) {
            num++
        }
        return num
    }

    function showEtablissementModal() {
        const nextIdToUse = getNextIdToUse()

        let template = document.getElementById('etablissement-template').innerHTML
        template = template.replace(/__prefix__/g, nextIdToUse.toString())
        document.getElementById("main-form").insertAdjacentHTML('beforeend', template)

        const modal = document.getElementById("fr-modal-etablissement" + nextIdToUse.toString())
        modal.setAttribute("data-etablissement-id", nextIdToUse.toString())
        modal.querySelector('[id$=raison_sociale]').required = true
        modal.querySelector(".save-btn").setAttribute("data-etablissement-id", nextIdToUse)
        setTimeout(() => {
            dsfr(modal).modal.disclose()
            dsfr(modal).modal.node.addEventListener('dsfr.conceal', event => {
                removeRequired(modal)
                if (!event.target.classList.contains("save-btn") && !!modalEtablissementHTMLContent[nextIdToUse]) {
                    event.target.querySelector(".fr-modal__content").replaceWith(modalEtablissementHTMLContent[nextIdToUse])
                    modalEtablissementHTMLContent[nextIdToUse] = null
                }
            });
        }, 10)

        const addressChoices = setUpAddressChoices(modal.querySelector('[id$=adresse_lieu_dit]'))
        addressChoices.passedElement.element.addEventListener("choice", (event)=> {
            modal.querySelector('[id$=commune]').value = event.detail.customProperties.city
            modal.querySelector('[id$=code_insee]').value = event.detail.customProperties.inseeCode
            if (!!event.detail.customProperties.context)
            {
                modal.querySelector('[id$=pays]').value = "FR"
                modal.querySelector('[id$=departement]').value = event.detail.customProperties.context.split(",")[1].trim()
            }
        })


        modal.querySelector("[id^=etablissement-save-btn-]").addEventListener("click", event => {
            event.preventDefault()
            submitFormAndAddEtablissementCard(event)
        })
    }

    function getSelectedLabel(element) {
        if (!element.value) {
            return null
        }
        return element.options[element.selectedIndex].innerText;
    }

    function getEtablissementCard(baseCard, currentModal, currentID){

        if (!!baseCard.querySelector(".etablissement-card")){
            baseCard.querySelector(".etablissement-card").id = `etablissement-card-${currentID}`
        }
        baseCard.querySelector('.raison-sociale').textContent = currentModal.querySelector('[id$=raison_sociale]').value

        const typeExploitant = getSelectedLabel(currentModal.querySelector('[id$=type_exploitant]'))
        if (typeExploitant != null) {
            baseCard.querySelector('.type-exploitant').innerText = typeExploitant
            baseCard.querySelector('.type-exploitant').classList.remove("fr-hidden")
        }

        const pays = getSelectedLabel(currentModal.querySelector('[id$=pays]'))
        if (pays != null) {
            baseCard.querySelector('.pays').innerText = pays
            baseCard.querySelector('.pays').classList.remove("fr-hidden")
        }

        const structure = `Département : ${currentModal.querySelector('[id$=departement]').value || 'nc.'}`
        baseCard.querySelector('.structure').textContent = structure

        const numeroAgrement = `N° d'agrément : ${currentModal.querySelector('[id$=numero_agrement]').value || 'nc.'}`
        baseCard.querySelector('.numero-agrement').textContent = numeroAgrement

        const positionDossierInput = currentModal.querySelector('[id$=position_dossier]')
        const positionDossier = getSelectedLabel(positionDossierInput)
        if (positionDossier != null) {
            baseCard.querySelector('.position-dossier').innerText = positionDossier
            baseCard.querySelector('.position-dossier').classList.remove("fr-hidden")
            const extraClass = positionDossierInput.options[positionDossierInput.selectedIndex].dataset.extraClass
            baseCard.querySelector('.position-dossier').classList.add(extraClass)
        }
        return baseCard
    }

    function deleteEtablissement(etablissementID){
        document.getElementById(`etablissement-card-${etablissementID}`).remove()
        document.getElementById(`fr-modal-etablissement${etablissementID}`).remove()
        document.querySelector(`[aria-controls="fr-modal-etablissement${etablissementID}"]`).remove()
    }

    function submitFormAndAddEtablissementCard(event) {
        const currentModal = event.target.closest("dialog")
        if (formIsValid(currentModal) === false) {
            return
        }

        const etablissementId = event.target.dataset.etablissementId
        const existingCard = document.getElementById(`etablissement-card-${etablissementId}`)

        if(!existingCard){
            const clone = document.getElementById('etablissement-card-template').content.cloneNode(true);
            const card = getEtablissementCard(clone, currentModal, etablissementId)
            card.querySelector('.etablissement-delete-btn').addEventListener("click", () => {deleteEtablissement(etablissementId)})
            card.querySelector('.etablissement-edit-btn').setAttribute("aria-controls", `fr-modal-etablissement${etablissementId}`)
            card.querySelector('.etablissement-edit-btn').addEventListener("click", () => {
                modalEtablissementHTMLContent[etablissementId] = document.querySelector(`#fr-modal-etablissement${etablissementId} .fr-modal__content`).cloneNode(true)
            })
            document.getElementById("etablissement-card-container").appendChild(card);
        } else {
            existingCard.replaceWith(getEtablissementCard(existingCard, currentModal, etablissementId))
        }

        dsfr(currentModal).modal.conceal()
        removeRequired(currentModal)
    }

    document.getElementById('add-etablissement').addEventListener("click", event => {
        event.preventDefault()
        showEtablissementModal()
    })
});
