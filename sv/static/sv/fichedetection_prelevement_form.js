document.prelevementCards =[]
let extraFormSaved = 0
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

function showOrHidePrelevementUI(){
    if (document.getElementById("lieux-list").childElementCount === 0){
        document.getElementById("no-lieux-text").classList.remove("fr-hidden")
        document.getElementById("btn-add-prelevment").disabled = true
    } else {
        document.getElementById("no-lieux-text").classList.add("fr-hidden")
        document.getElementById("btn-add-prelevment").disabled = false
    }
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
        clone.querySelector('.prelevement-type').textContent = `${card.officiel} | ${card.detecte}`;
        clone.querySelector('.prelevement-delete-btn').setAttribute("data-id", card.id)
        clone.querySelector(".prelevement-edit-btn").setAttribute("aria-controls", "modal-add-edit-prelevement-" + card.id)
        clone.querySelector('.prelevement-delete-btn').addEventListener("click", (event)=>{
            dsfr(document.getElementById("modal-delete-prelevement-confirmation")).modal.disclose()
            document.getElementById("delete-prelevement-confirm-btn").setAttribute("data-id", event.target.dataset.id)
        })
        prelevementListElement.appendChild(clone);
    })
    showOrHidePrelevementUI()
}

function showAddPrelevementmodal(event) {
    event.preventDefault()
    const currentModal = document.getElementById("modal-add-edit-prelevement-" + extraFormSaved)
    modalHTMLContent[extraFormSaved] = currentModal.querySelector(".fr-modal__content").innerHTML
    const selectElement = document.getElementById('id_prelevements-' + extraFormSaved + "-lieu");
    selectElement.innerHTML = '';
    document.lieuxCards.forEach(option => {
        const opt = document.createElement('option');
        opt.value = option.nom;
        opt.textContent = option.nom;
        selectElement.appendChild(opt);
    });

    currentModal.querySelectorAll('input, textarea, select').forEach((input) =>{
        if (input.hasAttribute("data-required")){
            input.required = true
        }
    })
    dsfr(currentModal).modal.disclose();
    dataRequiredToRequired(currentModal)
}

function savePrelevement(event){
    const id = event.target.dataset.id
    const modal = document.getElementById(`modal-add-edit-prelevement-${id}`)
    if (formIsValid(modal) === false){
        return
    }

    const structureElement = document.getElementById(`id_prelevements-${id}-structure_preleveur`)
    const lieuElement = document.getElementById(`id_prelevements-${id}-lieu`)
    const officielElement = document.getElementById(`id_prelevements-${id}-is_officiel`)
    const resultatElement = document.querySelector('input[name="prelevements-' + id + '-resultat"]:checked')
    let data = {
        "id": id,
        "structure":structureElement.options[structureElement.selectedIndex].text,
        "lieu": lieuElement.options[lieuElement.selectedIndex].text,
        "officiel":  officielElement.checked === true ? "Prélèvement officiel" : "Prélèvement non officiel",
        "detecte": resultatElement.value === "detecte" ? "DÉTECTÉ" : "NON DÉTECTÉ"
    }

    const index = document.prelevementCards.findIndex(element => element.id === data.id);
    if (index === -1) {
        document.prelevementCards.push(data);
        extraFormSaved++;
    } else {
        document.prelevementCards[index] = data;
    }

    displayPrelevementsCards()
    removeRequired(modal)
    dsfr(modal).modal.conceal();

}

function resetModalWhenClosing(event){
    const originalTarget = event.explicitOriginalTarget
    if (! originalTarget.classList.contains("prelevement-save-btn")){
        const modalId = event.originalTarget.getAttribute("id").split("-").pop()
        event.originalTarget.querySelector(".fr-modal__content").innerHTML = modalHTMLContent[modalId]
    }
}

(function() {
    showOrHidePrelevementUI()
    document.getElementById("btn-add-prelevment").addEventListener("click", showAddPrelevementmodal)
    document.getElementById("delete-prelevement-confirm-btn").addEventListener("click", deletePrelevement)
    document.querySelectorAll(".prelevement-save-btn").forEach(button => button.addEventListener("click", savePrelevement))
    document.querySelectorAll("select[id$=espece-echantillon]").forEach(element => addChoicesEspeceEchantillon(element))
    document.querySelectorAll("[id^=modal-add-edit-prelevement-]").forEach(modal => modal.addEventListener('dsfr.conceal', resetModalWhenClosing))
    document.querySelectorAll("[id^=modal-add-edit-prelevement-] .fr-btn--close").forEach(element => element.addEventListener("click", closeDSFRModal))
})();

// TODO vérifier qu'a l'ouverture on refait pas le choices pour la l'espece et autre champ choices
