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
    resetForm(document.getElementById("modal-add-lieu-" + id))
    displayLieuxCards()
    dsfr(document.getElementById('modal-delete-lieu-confirmation')).modal.conceal();
}

function displayLieuxCards() {
    const lieuListElement = document.getElementById("lieux-list")
    const lieuTemplateElement = document.getElementById("lieu-carte")
    lieuListElement.innerHTML = ""
    if (document.lieuxCards.length === 0) {
        lieuListElement.innerHTML = "Aucun lieu."
        return
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
    dataRequiredToRequired(currentModal)
    dsfr(currentModal).modal.disclose();
}

function buildLieuCardFromModal(element){
    return {
        "id": element.dataset.id,
        "nom": element.querySelector(`[id^="id_lieux-"][id$="-nom"]`).value,
        "commune": element.querySelector(`[id^="commune-select-"]`).value,
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
        extraFormSaved++;
    } else {
        document.lieuxCards[index] = buildLieuCardFromModal(modal);
    }

    displayLieuxCards()
    removeRequired(modal)
    dsfr(modal).modal.conceal()
    modal.querySelector(".fr-modal__title").textContent = "Modifier le lieu"
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
        const currentModal = Array.from(document.querySelectorAll(".fr-modal")).find(el => getComputedStyle(el).display !== "none");
        currentModal.querySelector('[id$=commune]').value = event.detail.choice.value
        currentModal.querySelector('[id$=insee]').value = event.detail.choice.customProperties.inseeCode
        currentModal.querySelector('[id$=departement]').value = event.detail.choice.customProperties.departementCode
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
    // TODO what to do in this case ?
}

(function() {
    document.querySelector("#add-lieu-bouton").addEventListener("click", showLieuModal)
    document.querySelectorAll(".lieu-save-btn").forEach(button => button.addEventListener("click", saveLieu))
    document.querySelectorAll("[id^=commune-select-]").forEach(setUpCommune)
    document.getElementById("delete-lieu-confirm-btn").addEventListener("click", deleteLieu)
    document.querySelectorAll("[id^=modal-add-lieu-]").forEach(modal => modal.addEventListener('dsfr.conceal', resetModalWhenClosing))
    document.querySelectorAll("[id^=modal-add-lieu-]").forEach(modal => modal.addEventListener('dsfr.disclose', saveModalWhenOpening))
    document.querySelectorAll("[id^=modal-add-lieu-] .fr-btn--close").forEach(element => element.addEventListener("click", closeDSFRModal))
    document.querySelectorAll("[id^=modal-add-lieu-] .lieu-cancel-btn").forEach(element => element.addEventListener("click", closeDSFRModal))

    document.querySelectorAll("[id^=modal-add-lieu-]").forEach(element =>{
        const data = buildLieuCardFromModal(element)
        if (!!data.nom){
            document.lieuxCards.push(data)
        }
    })
    // TODO edit on page with no lieux and prelevements gives JS error
    displayLieuxCards()

})();
