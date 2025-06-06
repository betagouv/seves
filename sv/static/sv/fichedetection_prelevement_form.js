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
        placeholderValue: 'Tapez minimum 2 caractères',
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
        if (query.length >= 2) {
            fetchEspecesEchantillon(query).then(results => {
                choicesEspece.clearChoices()
                choicesEspece.setChoices(results, 'value', 'label', true)
            })
        }
    })
    return choicesEspece
}

/** @param {MouseEvent} evt */
function duplicatePrelevement (evt) {
    evt.preventDefault()
    evt.stopPropagation()
    const elToClone = document.querySelector(`#modal-add-edit-prelevement-${evt.target.dataset.id}`)
    const currentModal = getNextAvailablePrelevementModal();
    [
        "numero_rapport_inspection",
        "numero_echantillon",
        "lieu",
        "structure_preleveuse",
        "matrice_prelevee",
        "date_prelevement",
    ].forEach(it => {
        const src = elToClone.querySelector(`[name$="${it}"]`)
        currentModal.querySelector(`[name$="${it}"]`).value = src.value
    });
    // espece_echantillon form element is a bit special; its options are populated via HTTP query
    // so we have not choice but to entirely clone the field here
    currentModal.querySelector("#espece-echantillon").innerHTML = (
        elToClone.querySelector("#espece-echantillon").innerHTML
    );
    modalHTMLContent[currentModal.dataset.id] = currentModal.querySelector(".fr-modal__content").innerHTML
    populateLieuSelect(currentModal.querySelector(`[id^="id_prelevements-"][id$="-lieu"]`))
    dataRequiredToRequired(currentModal)
    dsfr(currentModal).modal.disclose();
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
        if(card.type === "premiere_intention") {
            if(clone.querySelector(".prelevement-duplicate-btn") === null) {
                clone.querySelector("#action-btns").insertAdjacentHTML(
                    "beforeend", document.querySelector("#prelevement-duplicate-btn-tpl").innerHTML
                );
            }

            const el = clone.querySelector('.prelevement-copy-btn')
            el.setAttribute("data-id", card.id)
            el.setAttribute("aria-describedby", `tooltip-duplicate-prelevement-${card.id}`)
            el.setAttribute("aria-controls", `modal-duplicate-prelevement-${card.id}`)
            el.addEventListener("click", duplicatePrelevement)
            clone.querySelector('.duplicate-tooltip').setAttribute("id", `tooltip-duplicate-prelevement-${card.id}`)
        } else {
            clone.querySelectorAll(".prelevement-duplicate-btn").forEach(it => it.remove())
        }
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
    const typeElement = element.querySelector(`[id^="id_prelevements-"][id*="-type_analyse"]:checked`)
    const structureElement = element.querySelector(`[id^="id_prelevements-"][id$="-structure_preleveuse"]`)
    const lieuElement = element.querySelector(`[id^="id_prelevements-"][id$="-lieu"]`)
    const officielElement = element.querySelector(`[id^="id_prelevements-"][id$="-is_officiel"]`)
    const resultatElement = element.querySelector(`input[name*="-resultat"]:checked`)
    const resultats = JSON.parse(document.getElementById("prelevement-resultats").textContent);
    return {
        "id": element.dataset.id,
        "type": typeElement.value,
        "structure":structureElement.options[structureElement.selectedIndex].text,
        "lieu": lieuElement.options[lieuElement.selectedIndex].text,
        "officiel":  officielElement.checked === true ? "Prélèvement officiel" : "Prélèvement non officiel",
        "resultat": resultats[resultatElement.value].toUpperCase()
    }
}

function showModalIfPrelevementEnAttente(resultat) {
    if (resultat === "EN ATTENTE"){
        dsfr(document.getElementById("fr-modal-prelevement-en-attente")).modal.disclose();
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
    showModalIfPrelevementEnAttente(data.resultat);
}

function saveModalWhenOpening(event){
    const modalId = event.target.getAttribute("id").split("-").pop()
    populateLieuSelect(event.target.querySelector((`[id^="id_prelevements-"][id$="-lieu"]`)))
    // On ne sauvegarde que si ce n'est pas déjà fait (cas de la modification)
    if (!modalHTMLContent[modalId]) {
        modalHTMLContent[modalId] = event.target.querySelector(".fr-modal__content").innerHTML
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
    handleChangeIsOfficiel(event)
}

function handleChangeTypeAnalyse(event){
    setIsOfficiel(event)
    const laboElement =  event.target.closest("dialog").querySelector("[id$=laboratoire]")
    const isConfirmation = event.target.value === "confirmation"

    laboElement.querySelectorAll('option').forEach(option => {
        option.disabled = isConfirmation && option.getAttribute('data-confirmation-officielle') === 'false'
    });
}

function handleChangeIsOfficiel(event){
    const isOfficielCheckbox = event.target.closest("dialog").querySelector("[id$=is_officiel]")
    const numeroRIElement =  event.target.closest("dialog").querySelector("[id$=numero_rapport_inspection]")
    if (isOfficielCheckbox.checked === false){
        numeroRIElement.value = ""
        numeroRIElement.disabled = true
    } else {
        numeroRIElement.disabled = false
    }
}

function handleModalClose(event) {
    const modal = event.target.closest('dialog');
    const modalId = modal.id.split('-').pop();
    const modalContent = modal.querySelector('.fr-modal__content');
    // Réinitialise le contenu
    if (modalContent && modalHTMLContent[modalId]) {
        modalContent.innerHTML = modalHTMLContent[modalId];
    }
    dsfr(modal).modal.conceal();
}

(function() {
    showOrHidePrelevementUI()
    document.getElementById("btn-add-prelevment").addEventListener("click", showAddPrelevementmodal)
    document.getElementById("delete-prelevement-confirm-btn").addEventListener("click", deletePrelevement)
    document.querySelectorAll(".prelevement-save-btn").forEach(button => button.addEventListener("click", savePrelevement))
    document.querySelectorAll("select[id$=espece-echantillon]").forEach(element => addChoicesEspeceEchantillon(element))
    document.querySelectorAll("select[id$=structure_preleveuse]").forEach(element => element.addEventListener("change", setIsOfficiel))
    document.querySelectorAll("input[name$=type_analyse]").forEach(element => element.addEventListener("change", handleChangeTypeAnalyse))
    document.querySelectorAll("input[name$=is_officiel]").forEach(element => element.addEventListener("change", handleChangeIsOfficiel))
    document.querySelectorAll("[id^=modal-add-edit-prelevement-]").forEach(modal => modal.addEventListener('dsfr.disclose', saveModalWhenOpening))
    document.querySelectorAll("[id^=modal-add-edit-prelevement-] .fr-btn--close, [id^=modal-add-edit-prelevement-] .prelevement-cancel-btn")
        .forEach(button => button.addEventListener('click', handleModalClose));

    document.querySelectorAll("[id^=modal-add-edit-prelevement-]").forEach(element =>{
        if (element.dataset.alreadyExisting){
            const data = buildPrelevementCardFromModal(element)
            document.prelevementCards.push(data)
        }
    })
    displayPrelevementsCards()

})();
