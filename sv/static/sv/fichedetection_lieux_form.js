document.lieuxCards = []
modalHTMLContent = {}

function fetchCommunes(query) {
    return fetch(`https://geo.api.gouv.fr/communes?nom=${query}&fields=departement&boost=population&limit=15`)
        .then(response => response.json())
        .then(data => {
            return data.map(item => ({
                value: item.nom,
                label: `${item.nom} (${item.departement.code})` ,
                customProperties: {
                    "departementCode": item.departement.code,
                    "inseeCode": item.code
                }
            }))
        })
        .catch(error => {
            console.error('Erreur lors de la récupération des données:', error);
            return []
        });
}

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
    setUpCommune(currentModal.querySelector("[id^=commune-select-]"))
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
    const choicesCommunes = new Choices(element, {
        removeItemButton: true,
        placeholderValue: 'Recherchez...',
        noResultsText: 'Aucun résultat trouvé',
        noChoicesText: 'Aucun résultat trouvé',
        shouldSort: false,
        searchResultLimit: 10,
        classNames: {containerInner: 'fr-select'},
        itemSelectText: '',
    });

    const currentModal = element.closest("dialog");
    const communeInput = currentModal.querySelector('[id$=commune]');
    const inseeInput = currentModal.querySelector('[id$=code_insee]');
    const departementInput = currentModal.querySelector('[id$=departement]');

    setupPreselection(choicesCommunes, communeInput, departementInput, inseeInput);

    choicesCommunes.input.element.addEventListener('input', function (event) {
        const query = choicesCommunes.input.element.value
        if (query.length > 2) {
            fetchCommunes(query).then(results => {
                choicesCommunes.clearChoices()
                choicesCommunes.setChoices(results, 'value', 'label', true)
            })
        }
    })

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


function fetchSiret(value, token) {
    const url = 'https://api.insee.fr/entreprises/sirene/siret?q=siren%3A' + value.replaceAll(" ", "")+ '* AND -periode(etatAdministratifEtablissement:F)';
    const headers = {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
    };
    let results = []
    return fetch(url, {method: 'GET', headers: headers})
        .then(response => response.json())
        .then(data => {
            if (!data["etablissements"]){
                return []
            }
            data["etablissements"].forEach((etablissement) => {
                let address = etablissement["adresseEtablissement"]
                let streetData = `${address["numeroVoieEtablissement"]} ${address["typeVoieEtablissement"]} ${address["libelleVoieEtablissement"]} - ${address["codePostalEtablissement"]} ${address["libelleCommuneEtablissement"]}`
                let resultEtablissement = `${etablissement["siret"]} - ${streetData}`
                const uniteLegale = etablissement["uniteLegale"]
                let resultUnite = `${uniteLegale["denominationUniteLegale"]?? ""} ${uniteLegale["denominationUniteLegale"]?? ""} ${uniteLegale["prenom1UniteLegale"]?? ""} ${uniteLegale["nomUniteLegale"]?? ""}`
                results.push({
                    value: etablissement["siret"],
                    label: resultUnite + " " + resultEtablissement ,
                    customProperties: {
                        "streetData": streetData,
                        "siret": etablissement["siret"],
                        "raison": uniteLegale["denominationUniteLegale"]
                    }
                })
            });
            return results
        });
}

function debounce(func, wait) {
    let timeout;
    return function (...args) {
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(this, args), wait);
    };
}

function configureSiretField(field){
    const choicesSIRET = new Choices(field, {
        removeItemButton: true,
        placeholderValue: 'N° SIRET',
        noResultsText: 'Aucun résultat trouvé',
        noChoicesText: 'Aucun résultat trouvé',
        shouldSort: false,
        searchResultLimit: 20,
        classNames: {containerInner: 'fr-select'},
        itemSelectText: '',
        position: 'top',
    });

    choicesSIRET.input.element.addEventListener('input', debounce((event) => {
        const query = choicesSIRET.input.element.value
        if (query.length > 5) {
            fetchSiret(query, field.dataset.token).then(results => {
                choicesSIRET.clearChoices()
                choicesSIRET.setChoices(results, 'value', 'label', true)
            })
        }
    }, 300))

    choicesSIRET.passedElement.element.addEventListener("choice", (event)=> {
        field.closest("dialog").querySelector('[id$=siret_etablissement]').value = event.detail.customProperties.siret
        field.closest("dialog").querySelector('[id$=raison_sociale_etablissement]').value = event.detail.customProperties.raison
        field.closest("dialog").querySelector('[id$=adresse_lieu_dit]').value = event.detail.customProperties.streetData
        field.closest("dialog").querySelector('[id$=adresse_etablissement]').value = event.detail.customProperties.streetData
        field.closest("dialog").querySelector('[id$=pays_etablissement]').value = "France"

        field.closest("dialog").querySelector('[id$=sirene-btn]').classList.remove("fr-hidden")
        field.closest("dialog").querySelector('.fr-search-bar').classList.add("fr-hidden")
        field.closest("dialog").querySelector('.fr-search-bar select').innerHTML = ""
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
    document.querySelectorAll("[id^=commune-select-]").forEach(communeSelect =>{
        const communeField = communeSelect.parentNode.parentNode.querySelector('[id$="-commune"]')
        if (!!communeField.value){
            setUpCommune(communeSelect)
        }
    })
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
