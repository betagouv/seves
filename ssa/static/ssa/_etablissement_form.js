import {setUpAddressChoices} from "BanAutocomplete";
import {setUpSiretChoices} from "/static/core/siret.js";

let modalEtablissementHTMLContent = {}

document.addEventListener('DOMContentLoaded', () => {
    function getNextIdToUse() {
        let num = 0
        while (document.getElementById(`id_ssa-etablissement-content_type-object_id-${num}-raison_sociale`)) {
            num++
        }
        return num
    }

    function setupAdresseField(modal){
        const addressChoices = setUpAddressChoices(modal.querySelector('[id$=adresse_lieu_dit]'))
        addressChoices.passedElement.element.addEventListener("choice", (event)=> {
            modal.querySelector('[id$=commune]').value = event.detail.customProperties.city
            modal.querySelector('[id$=code_insee]').value = event.detail.customProperties.inseeCode
            if (!!event.detail.customProperties.context)
            {
                modal.querySelector('[id$=pays]').value = "FR"
                const [num, dept, reg, ...rest] = event.detail.customProperties.context.split(/\s*,\s*/)
                modal.querySelector('[id$=departement]').value = num
            }
        })
        return addressChoices
    }

    function configureSiretField(field, addressChoices, communesApi){
        const choicesSIRET = setUpSiretChoices(field, 'bottom')
        choicesSIRET.passedElement.element.addEventListener("choice", (event)=> {
            const codeCommune = event.detail.customProperties.code_commune;
            field.closest("dialog").querySelector('[id$=siret]').value = event.detail.customProperties.siret
            field.closest("dialog").querySelector('[id$=raison_sociale]').value = event.detail.customProperties.raison
            field.closest("dialog").querySelector('[id$=commune]').value = event.detail.customProperties.commune
            field.closest("dialog").querySelector('[id$=code_insee]').value = codeCommune
            field.closest("dialog").querySelector('[id$=pays]').value = "FR"

            if (!!event.detail.customProperties.streetData){
                let result = [{"value": event.detail.customProperties.streetData, "label": event.detail.customProperties.streetData, selected:true }]
                addressChoices.setChoices(result, 'value', 'label', true)
            }

            fetch(`/ssa/api/find-numero-agrement/?siret=${event.detail.customProperties.siret}`)
                .then(response => response.json())
                .then(data => {
                    if (!!data["numero_agrement"]){
                        field.closest("dialog").querySelector('[id$=agrement]').value = data["numero_agrement"]
                    }
                });

            if (!!codeCommune && !!communesApi) {
                fetch(`${communesApi}/${codeCommune}?fields=departement`).then(async response => {
                    const json = await response.json();
                    field.closest("dialog").querySelector('[id$=departement]').value = json.departement.code;
                })
            }
        })
    }

    function setupSiretBlock(modal, addressChoices){
        const siretSelect = modal.querySelector("[id^=search-siret-input-]")
        if (!siretSelect.dataset.token){
            return
        }

        configureSiretField(siretSelect, addressChoices, siretSelect.dataset.communesApi)
    }

    function setupEtablisementModal(modal){
        let addressChoices = setupAdresseField(modal)
        setupSiretBlock(modal, addressChoices)

        modal.querySelector("[id^=etablissement-save-btn-]").addEventListener("click", event => {
            event.preventDefault()
            submitFormAndAddEtablissementCard(event)
        })
    }

    function showEtablissementModal() {
        const nextIdToUse = getNextIdToUse()

        let template = document.getElementById('etablissement-template').innerHTML
        template = template.replace(/__prefix__/g, nextIdToUse.toString())
        document.getElementById("main-form").insertAdjacentHTML('beforeend', template)

        const modal = document.getElementById("fr-modal-etablissement" + nextIdToUse.toString())
        modal.querySelector('[id$=raison_sociale]').required = true
        modal.querySelector('.save-btn').dataset.etablissementId = nextIdToUse

        setTimeout(() => {
            dsfr(modal).modal.disclose()
            dsfr(modal).modal.node.addEventListener('dsfr.conceal', event => {
                if (modal.dataset.needsRestoreBackup === "false"){
                    modal.dataset.needsRestoreBackup = ""
                    removeRequired(modal)
                    return
                }
                removeRequired(modal)
                if (!!modalEtablissementHTMLContent[nextIdToUse]) {
                    event.target.querySelector(".fr-modal__content").replaceWith(modalEtablissementHTMLContent[nextIdToUse])
                    modalEtablissementHTMLContent[nextIdToUse] = null
                }
            });
        }, 10)

        setupEtablisementModal(modal)
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

        const typeExploitant = currentModal.querySelector('[id$=type_exploitant]').value
        if (typeExploitant != null) {
            baseCard.querySelector('.type-exploitant').innerText = typeExploitant
            baseCard.querySelector('.type-exploitant').classList.remove("fr-hidden")
        }

        const pays = getSelectedLabel(currentModal.querySelector('[id$=pays]'))
        if (pays != null) {
            baseCard.querySelector('.pays').innerText = pays
            baseCard.querySelector('.pays').classList.remove("fr-hidden")
        }

        try {
            const select = currentModal.querySelector('[id$=departement]');
            const option = select.options[select.selectedIndex];
            baseCard.querySelector('.structure').textContent = `Département : ${option.innerText}`;
        } catch {
            baseCard.querySelector('.structure').textContent = '<span class="empty-value">Vide</span>';
        }

        const numeroAgrementValue = currentModal.querySelector('[id$=numero_agrement]').value
        if (!!numeroAgrementValue) {
            baseCard.querySelector('.numero-agrement').textContent = `N° d'agrément : ${numeroAgrementValue}`
            baseCard.querySelector('.numero-agrement').classList.remove("fr-hidden")
        } else {
            baseCard.querySelector('.numero-agrement').classList.add("fr-hidden")
        }


        const positionDossierInput = currentModal.querySelector('[id$=position_dossier]')
        const positionDossier = getSelectedLabel(positionDossierInput)
        if (positionDossier != null) {
            baseCard.querySelector('.position-dossier').innerText = positionDossier
            baseCard.querySelector('.position-dossier').classList.remove("fr-hidden")
            const extraClass = positionDossierInput.options[positionDossierInput.selectedIndex].dataset.extraClass
            const basePositionDossier = baseCard.querySelector('.position-dossier')
            if (!!extraClass){
                basePositionDossier.classList.add(extraClass)
            } else {
                basePositionDossier.classList.value = basePositionDossier.dataset.resetClasses
            }
        }
        return baseCard
    }

    function deleteEtablissement(etablissementID){
        const etablissementModal = document.getElementById(`fr-modal-etablissement${etablissementID}`)
        const exitingEtablissement = !!etablissementModal.querySelector('[id$=DELETE]')
        if(exitingEtablissement){
            etablissementModal.querySelector('[id$=DELETE]').checked = true
        } else {
            etablissementModal.remove()
        }
        document.getElementById(`etablissement-card-${etablissementID}`).remove()
        document.querySelector(`[aria-controls="fr-modal-etablissement${etablissementID}"]`).remove()
    }


    function initExistingEtablissements(){
        document.querySelectorAll('[id^="fr-modal-etablissement"]').forEach(element =>{
            const etablissementId = element.id.replace("fr-modal-etablissement", "")
            getAndAddCardToList(element, etablissementId)
            setupEtablisementModal(element)
            element.querySelector('[id$=raison_sociale]').required = true
        })
    }

    function getAndAddCardToList(currentModal, etablissementId){
        const clone = document.getElementById('etablissement-card-template').content.cloneNode(true);
        const card = getEtablissementCard(clone, currentModal, etablissementId)
        card.querySelector('.etablissement-delete-btn').addEventListener("click", () => {deleteEtablissement(etablissementId)})
        card.querySelector('.etablissement-edit-btn').setAttribute("aria-controls", `fr-modal-etablissement${etablissementId}`)
        card.querySelector('.etablissement-edit-btn').addEventListener("click", () => {
            modalEtablissementHTMLContent[etablissementId] = document.querySelector(`#fr-modal-etablissement${etablissementId} .fr-modal__content`).cloneNode(true)
        })
        document.getElementById("etablissement-card-container").appendChild(card);

    }

    function submitFormAndAddEtablissementCard(event) {
        const currentModal = event.target.closest("dialog")
        if (formIsValid(currentModal) === false) {
            return
        }

        const etablissementId = event.target.dataset.etablissementId
        const existingCard = document.getElementById(`etablissement-card-${etablissementId}`)

        if(!existingCard){
            getAndAddCardToList(currentModal, etablissementId)
        } else {
            existingCard.replaceWith(getEtablissementCard(existingCard, currentModal, etablissementId))
        }

        dsfr(currentModal).modal.conceal()
        currentModal.dataset.needsRestoreBackup = "false"
        removeRequired(currentModal)
    }

    document.getElementById('add-etablissement').addEventListener("click", event => {
        event.preventDefault()
        showEtablissementModal()
    })
    initExistingEtablissements()
});
