document.lieuxCards = []
extraFormSaved = 0

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
        clone.querySelector(".lieu-edit-btn").setAttribute("aria-controls", "modal-add-lieu-" + card.id)
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
    const currentModal = document.getElementById("modal-add-lieu-" + extraFormSaved)
    dataRequiredToRequired(currentModal)
    dsfr(currentModal).modal.disclose();
}

function saveLieu(event){
    const id = event.target.dataset.id
    const modal = document.getElementById(`modal-add-lieu-${id}`)
    const isValid = formIsValid(modal)
    if (isValid === false){
        return
    }

    let data = {
        "id": id,
        "nom": document.getElementById(`id_lieux-${id}-nom`).value,
        "commune": document.getElementById(`commune-select-${id}`).value
    }

    const index = document.lieuxCards.findIndex(element => element.id === data.id);
    if (index === -1) {
        document.lieuxCards.push(data);
        extraFormSaved++;
    } else {
        document.lieuxCards[index] = data;
    }

    displayLieuxCards()
    removeRequired(modal)
    dsfr(modal).modal.conceal();
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

(function() {
    document.querySelector("#add-lieu-bouton").addEventListener("click", showLieuModal)
    document.querySelectorAll(".lieu-save-btn").forEach(button => button.addEventListener("click", saveLieu))
    document.querySelectorAll("[id^=commune-select-]").forEach(setUpCommune)
    document.getElementById("delete-lieu-confirm-btn").addEventListener("click", deleteLieu)

    // TODO should we clear store of commune when the modal is closed ????
})();

// TODO gérer les fermetures du modale (annuler et fermer)
// TODO EDIter : ouvrir la modale, copier en cas d'annulation, remettre si annulation
// TODO Supprimer : Remettre la modale à zero ? Si on créé et supprime X lieu ça ne marchera plus :possibilité d'avoir une listes des ids déjàs utilisés
