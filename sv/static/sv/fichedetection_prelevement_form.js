document.prelevementCards =[]
modalHTMLContent = {}

function fetchEspecesEchantillon(query) {
    return fetch(`/sv/api/espece/recherche/?q=${query}`)
        .then(response => response.json())
        .then(data => {
            return data.results.map(item => ({
                value: item.id,
                label: item.name ,
            }))
        })
        .catch(error => {
            console.error('Erreur lors de la récupération des données:', error);
            return []
        });
}


function addChoicesEspeceEchantillon(element){
    const choicesEspece = new Choices(element, {
        removeItemButton: true,
        placeholderValue: 'Recherchez...',
        noResultsText: 'Aucun résultat trouvé',
        noChoicesText: 'Aucun résultat trouvé',
        shouldSort: false,
        searchResultLimit: 50,
        classNames: {containerInner: 'fr-select'},
        itemSelectText: '',
        position: 'top',
    });
    choicesEspece.input.element.addEventListener('input', function (event) {
        const query = choicesEspece.input.element.value
        if (query.length > 2) {
            fetchEspecesEchantillon(query).then(results => {
                choicesEspece.clearChoices()
                choicesEspece.setChoices(results, 'value', 'label', true)
            })
        }
    })
    return choicesEspece
}


function deletePrelevement(event) {
    const id = event.target.dataset.id
    document.prelevementCards = document.prelevementCards.filter(function(item) {return item.id !== id})
    resetForm(document.getElementById("modal-add-edit-prelevement-" + id))
    displayPrelevementsCards()
    dsfr(document.getElementById('modal-delete-prelevement-confirmation')).modal.conceal();
}

function displayPrelevementsCards() {
    const prelevementListElement = document.getElementById("prelevements-list")
    const prelevementTemplateElement = document.getElementById("prelevement-carte")
    prelevementListElement.innerHTML = ""
    document.prelevementCards.forEach(card =>{
        const clone = prelevementTemplateElement.cloneNode(true);
        clone.classList.remove('fr-hidden');
        clone.querySelector('.prelevement-nom').textContent = card.structure;
        clone.querySelector('.prelevement-lieu').textContent = "Lieu : " + card.lieu;
        clone.querySelector('.prelevement-type').textContent = `${card.officiel} | ${card.resultat}`;
        clone.querySelector('.prelevement-delete-btn').setAttribute("data-id", card.id)
        clone.querySelector('.prelevement-delete-btn').setAttribute("aria-describedby", "tooltip-delete-prelevement-" + card.id)
        clone.querySelector(".delete-tooltip").setAttribute("id", "tooltip-delete-prelevement-" + card.id)
        clone.querySelector(".prelevement-edit-btn").setAttribute("aria-controls", "modal-add-edit-prelevement-" + card.id)
        clone.querySelector(".prelevement-edit-btn").setAttribute("aria-describedby", "tooltip-prelevement-" + card.id)
        clone.querySelector(".edit-tooltip").setAttribute("id", "tooltip-prelevement-" + card.id)
        clone.querySelector('.prelevement-delete-btn').addEventListener("click", (event)=>{
            dsfr(document.getElementById("modal-delete-prelevement-confirmation")).modal.disclose()
            document.getElementById("delete-prelevement-confirm-btn").setAttribute("data-id", event.target.dataset.id)
        })
        prelevementListElement.appendChild(clone);
    })
    showOrHidePrelevementUI()
}

function populateLieuSelect(element){
    element.innerHTML = '';
    document.lieuxCards.forEach(option => {
        const opt = document.createElement('option');
        opt.value = option.nom;
        opt.textContent = option.nom;
        element.appendChild(opt);
    });
}

function getNextAvailablePrelevementModal() {
    const elements = document.querySelectorAll("[id^=modal-add-edit-prelevement-]")
    for (const element of elements) {
        const input = element.querySelector(`[id^="id_prelevements-"][id$="-structure_preleveuse"]`)
        if (input && input.value === "") {
            return element
        }
    }
}

function showAddPrelevementmodal(event) {
    event.preventDefault()
    const currentModal = getNextAvailablePrelevementModal()
    modalHTMLContent[currentModal.dataset.id] = currentModal.querySelector(".fr-modal__content").innerHTML
    populateLieuSelect(currentModal.querySelector((`[id^="id_prelevements-"][id$="-lieu"]`)))

    dataRequiredToRequired(currentModal)
    dsfr(currentModal).modal.disclose();
}

function buildPrelevementCardFromModal(element){
    const structureElement = element.querySelector(`[id^="id_prelevements-"][id$="-structure_preleveuse"]`)
    const lieuElement = element.querySelector(`[id^="id_prelevements-"][id$="-lieu"]`)
    const officielElement = element.querySelector(`[id^="id_prelevements-"][id$="-is_officiel"]`)
    const resultatElement = element.querySelector(`input[name*="-resultat"]:checked`)
    const resultats = JSON.parse(document.getElementById("prelevement-resultats").textContent);
    return {
        "id": element.dataset.id,
        "structure":structureElement.options[structureElement.selectedIndex].text,
        "lieu": lieuElement.options[lieuElement.selectedIndex].text,
        "officiel":  officielElement.checked === true ? "Prélèvement officiel" : "Prélèvement non officiel",
        "resultat": resultats[resultatElement.value].toUpperCase()
    }
}

function savePrelevement(event){
    const id = event.target.dataset.id
    const modal = document.getElementById(`modal-add-edit-prelevement-${id}`)
    if (formIsValid(modal) === false){
        return
    }

    const data = buildPrelevementCardFromModal(modal)
    const index = document.prelevementCards.findIndex(element => element.id === data.id);
    if (index === -1) {
        document.prelevementCards.push(data);
    } else {
        document.prelevementCards[index] = data;
    }
    displayPrelevementsCards()
    removeRequired(modal)
    dsfr(modal).modal.conceal();
}

function saveModalWhenOpening(event){
    const modalId = event.target.getAttribute("id").split("-").pop()
    populateLieuSelect(event.target.querySelector((`[id^="id_prelevements-"][id$="-lieu"]`)))
    modalHTMLContent[modalId] = event.target.querySelector(".fr-modal__content").innerHTML
}


function resetModalWhenClosing(event){
    const originalTarget = event.explicitOriginalTarget
    if (! originalTarget.classList.contains("prelevement-save-btn")){
        const modalId = event.originalTarget.getAttribute("id").split("-").pop()
        event.originalTarget.querySelector(".fr-modal__content").innerHTML = modalHTMLContent[modalId]
    }
}

function setIsOfficiel(event){
    const modal = event.target.closest("dialog")
    const isOfficielCheckbox = modal.querySelector("[id$=is_officiel]")
    const structureElement = modal.querySelector("[id$=structure_preleveuse]")

    if(structureElement.options[structureElement.selectedIndex].text === "Exploitant"){
        isOfficielCheckbox.checked = false
        isOfficielCheckbox.disabled = true
        return
    }

    if (modal.querySelector("input[name$=type_analyse]:checked").value === "confirmation"){
        isOfficielCheckbox.checked = true
        isOfficielCheckbox.disabled = false
    }
}

function handleChangeTypeAnalyse(event){
    setIsOfficiel(event)
    const laboElement =  event.target.closest("dialog").querySelector("[id$=laboratoire]")
    const isConfirmation = event.target.value === "confirmation"

    laboElement.querySelectorAll('option').forEach(option => {
        option.disabled = isConfirmation && option.getAttribute('data-confirmation-officielle') === 'false'
    });
}

(function() {
    showOrHidePrelevementUI()
    document.getElementById("btn-add-prelevment").addEventListener("click", showAddPrelevementmodal)
    document.getElementById("delete-prelevement-confirm-btn").addEventListener("click", deletePrelevement)
    document.querySelectorAll(".prelevement-save-btn").forEach(button => button.addEventListener("click", savePrelevement))
    document.querySelectorAll("select[id$=espece-echantillon]").forEach(element => addChoicesEspeceEchantillon(element))
    document.querySelectorAll("select[id$=structure_preleveuse]").forEach(element => element.addEventListener("change", setIsOfficiel))
    document.querySelectorAll("input[name$=type_analyse]").forEach(element => element.addEventListener("change", handleChangeTypeAnalyse))
    document.querySelectorAll("[id^=modal-add-edit-prelevement-]").forEach(modal => modal.addEventListener('dsfr.conceal', resetModalWhenClosing))
    document.querySelectorAll("[id^=modal-add-edit-prelevement-]").forEach(modal => modal.addEventListener('dsfr.disclose', saveModalWhenOpening))
    document.querySelectorAll("[id^=modal-add-edit-prelevement-] .fr-btn--close").forEach(element => element.addEventListener("click", closeDSFRModal))
    document.querySelectorAll("[id^=modal-add-edit-prelevement-] .prelevement-cancel-btn").forEach(element => element.addEventListener("click", closeDSFRModal))
    document.querySelectorAll("[id^=modal-add-edit-prelevement-]").forEach(element =>{
        if (element.dataset.alreadyExisting){
            const data = buildPrelevementCardFromModal(element)
            document.prelevementCards.push(data)
        }
    })
    displayPrelevementsCards()

})();
