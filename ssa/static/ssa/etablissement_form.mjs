import {setUpAddressChoices} from "BanAutocomplete";
import {setUpSiretChoices} from "siret";
import {formIsValid, removeRequired} from "Forms"

let modalEtablissementHTMLContent = {}

const prefix = document.querySelector("#etablissement-template").dataset.prefix

document.addEventListener('DOMContentLoaded', () => {
    function getPrefix(id) {
        return prefix.replace(/__prefix__/g, id)
    }

    function getNextIdToUse() {
        const ids = document.querySelectorAll("dialog[data-form-prefix]").values().map(el => {
            try {
                return parseInt(el.dataset.formPrefix.match(/\d+/g)[0], 10)
            } catch {
                return Number.MIN_VALUE
            }
        });
        return Math.max(...ids, -1) + 1
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
        const prefix = getPrefix(nextIdToUse)

        let template = document.getElementById('etablissement-template').innerHTML
        template = template.replace(/__prefix__/g, nextIdToUse.toString())
        document.getElementById("main-form").insertAdjacentHTML('beforeend', template)

        const modal = document.getElementById(`fr-modal-etablissement-${prefix}`)
        modal.querySelector('[id$=raison_sociale]').required = true
        modal.querySelector('.save-btn').dataset.etablissementPrefix = prefix

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
            baseCard.querySelector(".etablissement-card").id = `etablissement-card-${getPrefix(currentID)}`
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
        const prefix = getPrefix(etablissementID)
        const etablissementModal = document.getElementById(`fr-modal-etablissement-${prefix}`)
        const exitingEtablissement = !!etablissementModal.querySelector('[id$=DELETE]')
        if(exitingEtablissement){
            etablissementModal.querySelector('[id$=DELETE]').value = "on"
        } else {
            etablissementModal.remove()
        }
        document.getElementById(`etablissement-card-${prefix}`).remove()
        document.querySelector(`[aria-controls="fr-modal-etablissement-${prefix}"]`).remove()
    }


    function initExistingEtablissements(){
        document.querySelectorAll('[id^="fr-modal-etablissement"]').forEach(element =>{
            const etablissementId = element.dataset.formPrefix.replace(getPrefix(""), "")
            getAndAddCardToList(element, etablissementId)
            setupEtablisementModal(element)
            element.querySelector('[id$=raison_sociale]').required = true
        })
    }

    function getAndAddCardToList(currentModal, etablissementId){
        const prefix = getPrefix(etablissementId)
        const clone = document.getElementById('etablissement-card-template').content.cloneNode(true);
        const card = getEtablissementCard(clone, currentModal, etablissementId)
        card.querySelector('.etablissement-delete-btn').addEventListener("click", () => {deleteEtablissement(etablissementId)})
        card.querySelector('.etablissement-edit-btn').setAttribute("aria-controls", `fr-modal-etablissement-${prefix}`)
        card.querySelector('.etablissement-edit-btn').addEventListener("click", () => {
            modalEtablissementHTMLContent[etablissementId] = document.querySelector(`#fr-modal-etablissement-${prefix} .fr-modal__content`).cloneNode(true)
        })
        document.getElementById("etablissement-card-container").appendChild(card);
        const totalForm = document.querySelector('#etablissement-management-form [name$="TOTAL_FORMS"]')
        totalForm.value = parseInt(totalForm.value, 10) + 1
    }

    function submitFormAndAddEtablissementCard(event) {
        const currentModal = event.target.closest("dialog")
        if (formIsValid(currentModal) === false) {
            return
        }

        const prefix = event.target.dataset.etablissementPrefix
        const etablissementId = prefix.replace(getPrefix(""), "")
        const existingCard = document.getElementById(`etablissement-card-${prefix}`)

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
