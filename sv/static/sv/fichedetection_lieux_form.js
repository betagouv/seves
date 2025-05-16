import {setUpSiretChoices} from "/static/core/siret.js";
import {setUpCommuneChoices} from "/static/core/commune.js";
import {setUpAddressChoices} from "/static/core/ban_autocomplete.js";

document.lieuxCards = []
modalHTMLContent = {}
document.choicesInstances = {};

function deleteLieu(event) {
    const id = event.target.dataset.id
    document.lieuxCards = document.lieuxCards.filter(function(item) {return item.id != id})
    const modal = document.getElementById("modal-add-lieu-" + id)
    resetForm(modal)
    if(!!modal.querySelector('[id$=DELETE]')){
        modal.querySelector('[id$=DELETE]').checked = true
    }
    displayLieuxCards()
    dsfr(document.getElementById('modal-delete-lieu-confirmation')).modal.conceal();
}

function displayLieuxCards() {
    const lieuListElement = document.getElementById("lieux-list")
    const lieuTemplateElement = document.getElementById("lieu-carte")
    lieuListElement.innerHTML = ""
    if (document.lieuxCards.length === 0) {
        lieuListElement.innerHTML = "Aucun lieu."
    }

    document.lieuxCards.forEach(card =>{
        const clone = lieuTemplateElement.cloneNode(true);
        clone.classList.remove('fr-hidden');
        clone.querySelector('.lieu-nom').textContent = card.nom;
        clone.querySelector('.lieu-commune').textContent = card.commune;
        clone.querySelector('.lieu-delete-btn').setAttribute("data-id", card.id)
        clone.querySelector('.lieu-delete-btn').setAttribute("aria-describedby", "tooltip-delete-lieu-" + card.id)
        clone.querySelector(".delete-tooltip").setAttribute("id", "tooltip-delete-lieu-" + card.id)
        clone.querySelector(".lieu-edit-btn").setAttribute("aria-controls", "modal-add-lieu-" + card.id)
        clone.querySelector(".lieu-edit-btn").setAttribute("aria-describedby", "tooltip-lieu-" + card.id)
        clone.querySelector(".edit-tooltip").setAttribute("id", "tooltip-lieu-" + card.id)
        clone.querySelector('.lieu-delete-btn').addEventListener("click", (event)=>{
            let lieuLinkedToPrelevement = document.prelevementCards.some(prelevement => prelevement.lieu === card.nom)
            if (lieuLinkedToPrelevement === true){
                dsfr(document.getElementById("fr-modal-suppression-lieu")).modal.disclose()
            } else {
                document.getElementById("delete-lieu-confirm-btn").setAttribute("data-id", event.target.dataset.id)
                dsfr(document.getElementById("modal-delete-lieu-confirmation")).modal.disclose()
            }
        })
        lieuListElement.appendChild(clone);
    })
    showOrHidePrelevementUI()
}

function showLieuModal(event){
    event.preventDefault()
    const currentModal = getNextAvailableModal()
    modalHTMLContent[currentModal.dataset.id] = currentModal.querySelector(".fr-modal__content").innerHTML
    dsfr(currentModal).modal.disclose()
    dataRequiredToRequired(currentModal)
}

function buildLieuCardFromModal(element){
    return {
        "id": element.dataset.id,
        "nom": element.querySelector(`[id^="id_lieux-"][id$="-nom"]`).value,
        "commune": element.querySelector(`[id^="id_lieux-"][id$="-commune"]`).value,
    }
}

function saveLieu(event){
    const id = event.target.dataset.id
    const modal = document.getElementById(`modal-add-lieu-${id}`)
    if (formIsValid(modal) === false){
        return
    }

    const index = document.lieuxCards.findIndex(element => element.id === id);
    if (index === -1) {
        document.lieuxCards.push(buildLieuCardFromModal(modal));
    } else {
        document.lieuxCards[index] = buildLieuCardFromModal(modal);
    }

    displayLieuxCards()
    removeRequired(modal)
    dsfr(modal).modal.conceal()
    modal.querySelector(".fr-modal__title").textContent = "Modifier le lieu"
}

function setupPreselection(choicesCommunes, communeInput, departementInput, inseeInput) {
    if (communeInput.value) {
        choicesCommunes.setChoiceByValue(communeInput.value);
        choicesCommunes.setChoices([{
            value: communeInput.value,
            label: `${communeInput.value} (${departementInput.value})`,
            selected: true,
            customProperties: {
                departementCode: departementInput.value,
                inseeCode: inseeInput.value
            }
        }], 'value', 'label', true);
    }
}

function setUpCommune(element) {
    const choicesCommunes = setUpCommuneChoices(element)

    const currentModal = element.closest("dialog");
    const communeInput = currentModal.querySelector('[id$=commune]');
    const inseeInput = currentModal.querySelector('[id$=code_insee]');
    const departementInput = currentModal.querySelector('[id$=departement]');

    setupPreselection(choicesCommunes, communeInput, departementInput, inseeInput);

    choicesCommunes.passedElement.element.addEventListener("choice", (event)=> {
        communeInput.value = event.detail.value
        inseeInput.value = event.detail.customProperties.inseeCode
        departementInput.value = event.detail.customProperties.departementCode
    })

    choicesCommunes.passedElement.element.addEventListener('removeItem', function (event) {
        communeInput.value = ""
        inseeInput.value = ""
        departementInput.value = ""
    })

    return choicesCommunes;
}

function onAdresseLieuChoice(event, modal, communeChoice) {
    communeChoice.setValue([event.detail.customProperties.city]);
    modal.querySelector('[id$=commune]').value = event.detail.customProperties.city;
    modal.querySelector('[id$=code_insee]').value = event.detail.customProperties.inseeCode;
    if (!!event.detail.customProperties.context) {
        modal.querySelector('[id$=departement]').value = event.detail.customProperties.context.split(",")[0].trim();
    }
}

function setUpAdresseLieu(modal, communeChoice) {
    const adresseLieuElement = modal.querySelector("[id$=adresse_lieu_dit]");
    const choicesAdresseLieu = setUpAddressChoices(adresseLieuElement);
    choicesAdresseLieu.passedElement.element.addEventListener("choice", (event) => onAdresseLieuChoice(event, modal, communeChoice));
}

function onAdresseEtablissementChoice(event, modal) {
    modal.querySelector('[id$=commune_etablissement]').value = event.detail.customProperties.city;
    modal.querySelector('[id$=code_insee_etablissement]').value = event.detail.customProperties.inseeCode;
    if (!!event.detail.customProperties.context) {
        modal.querySelector('[id$=pays_etablissement]').value = "FR";
        modal.querySelector('[id$=departement_etablissement]').value = event.detail.customProperties.context.split(",")[0].trim();
    }
}

function setUpAdresseEtablissement(modal) {
    const adresseEtablissementElement = modal.querySelector("[id$=adresse_etablissement]");
    const choicesAdresseEtablissement = setUpAddressChoices(adresseEtablissementElement);
    choicesAdresseEtablissement.passedElement.element.addEventListener("choice", (event) => onAdresseEtablissementChoice(event, modal));
    const modalId = modal.getAttribute("id").split("-").pop();
    document.choicesInstances[modalId] = {
        ...document.choicesInstances[modalId] || {},
        adresseEtablissement: choicesAdresseEtablissement
    };
}

function saveModalWhenOpening(event){
    const modalId = event.target.getAttribute("id").split("-").pop()
    modalHTMLContent[modalId] = event.target.querySelector(".fr-modal__content").innerHTML
}

function resetModalWhenClosing(event){
    const originalTarget = event.explicitOriginalTarget
    if (! originalTarget.classList.contains("lieu-save-btn")){
        const modalId = event.originalTarget.getAttribute("id").split("-").pop()
        event.originalTarget.querySelector(".fr-modal__content").innerHTML = modalHTMLContent[modalId]
    }
}
function getNextAvailableModal() {
    const elements = document.querySelectorAll("[id^=modal-add-lieu-]")
    for (const element of elements) {
        const input = element.querySelector(`[id^="id_lieux-"][id$="-nom"]`)
        if (input && input.value === "") {
            return element
        }
    }
}

function setupCharacterCounter(element) {
    const input = element.querySelector(`[id^="id_lieux-"][id$="-activite_etablissement"]`);
    let counterDiv = element.querySelector('.character-counter');
    const maxLength = input.getAttribute('maxlength');

    counterDiv.textContent = `${maxLength - input.value.length} caractères restants`;

    input.addEventListener('input', function(e) {
        const remaining = maxLength - e.target.value.length;
        counterDiv.textContent = `${remaining} caractères restants`;
    });
}


function configureSiretField(field){
    const modal = field.closest("dialog");
    const modalId = modal.getAttribute("id").split("-").pop();
    const choicesSIRET = setUpSiretChoices(field, 'top')
    choicesSIRET.passedElement.element.addEventListener("choice", (event)=> {
        modal.querySelector('[id$=siret_etablissement]').value = event.detail.customProperties.siret
        modal.querySelector('[id$=raison_sociale_etablissement]').value = event.detail.customProperties.raison
        modal.querySelector('[id$=adresse_lieu_dit]').value = event.detail.customProperties.streetData
        modal.querySelector('[id$=pays_etablissement]').value = "FR"
        if (document.choicesInstances[modalId] && document.choicesInstances[modalId].adresseEtablissement) {
            document.choicesInstances[modalId].adresseEtablissement.setValue([event.detail.customProperties.streetData]);
        }
        modal.querySelector('[id$=commune_etablissement]').value = event.detail.customProperties.commune
        modal.querySelector('[id$=departement_etablissement]').value = event.detail.customProperties.code_commune.substring(0, 2);
        modal.querySelector('[id$=code_insee_etablissement]').value = event.detail.customProperties.code_commune

        modal.querySelector('[id$=sirene-btn]').classList.remove("fr-hidden")
        modal.querySelector('.fr-search-bar').classList.add("fr-hidden")
        modal.querySelector('.fr-search-bar select').innerHTML = ""
        choicesSIRET.destroy()
    })
}

(function() {
    document.documentElement.addEventListener('dsfr.start', () => {
        setTimeout(() => {
            document.querySelectorAll("[id^=modal-add-lieu-]").forEach(modal => {
                dsfr(modal).modal.node.addEventListener('dsfr.conceal', resetModalWhenClosing);
            });
        }, 500);
    });

    document.querySelector("#add-lieu-bouton").addEventListener("click", showLieuModal)
    document.querySelectorAll(".lieu-save-btn").forEach(button => button.addEventListener("click", saveLieu))
    document.querySelectorAll("[id^=commune-select-]").forEach(communeSelect => {
        const modal = communeSelect.closest("dialog")
        const communeChoice = setUpCommune(communeSelect);
        setUpAdresseLieu(modal, communeChoice);
        setUpAdresseEtablissement(modal);
    });
    document.getElementById("delete-lieu-confirm-btn").addEventListener("click", deleteLieu)
    document.querySelectorAll("[id^=modal-add-lieu-]").forEach(modal => modal.addEventListener('dsfr.disclose', saveModalWhenOpening))
    document.querySelectorAll("[id^=modal-add-lieu-] .fr-btn--close").forEach(element => element.addEventListener("click", closeDSFRModal))
    document.querySelectorAll("[id^=modal-add-lieu-] .lieu-cancel-btn").forEach(element => element.addEventListener("click", closeDSFRModal))

    document.querySelectorAll("[id^=modal-add-lieu-]").forEach(element =>{
        setupCharacterCounter(element);
        const data = buildLieuCardFromModal(element)
        if (!!data.nom){
            document.lieuxCards.push(data)
        }
    })

    document.querySelectorAll(`[id$="-sirene-btn"]`).forEach(siretLookupBtn =>{
        if (!siretLookupBtn.nextElementSibling.querySelector("select").dataset.token){
            siretLookupBtn.classList.add("fr-hidden")
            return
        }

        siretLookupBtn.addEventListener("click", event =>{
            event.preventDefault()
            siretLookupBtn.classList.add("fr-hidden")
            configureSiretField(siretLookupBtn.nextElementSibling.querySelector("select"))
            siretLookupBtn.nextElementSibling.classList.remove("fr-hidden")
        })
    })
    displayLieuxCards()
})();
