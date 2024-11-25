document.lieuxCards = []

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
        clone.querySelector('.lieu-edit-btn').addEventListener("click", (event)=>{
            dsfr(document.getElementById("modal-add-lieu-" + card.id)).modal.disclose()
        })
        lieuListElement.appendChild(clone);
    })
    showOrHidePrelevementUI()
}

(function() {
    let extraFormSaved = 0
    document.querySelector("#add-lieu-bouton").addEventListener("click", function(event){
        event.preventDefault()
        const currentModal = document.getElementById("modal-add-lieu-" + extraFormSaved)
        dataRequiredToRequired(currentModal)
        dsfr(currentModal).modal.disclose();
    })

    document.querySelectorAll(".lieu-save-btn").forEach(button => button.addEventListener("click", function(event){
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
    }))
    // TODO gérer les fermetures du modale (annuler et fermer)
    // TODO EDIter : ouvrir la modale, copier en cas d'annulation, remettre si annulation
    // TODO Supprimer : Remettre la modale à zero ? Si on créé et supprime X lieu ça ne marchera plus :possibilité d'avoir une listes des ids déjàs utilisés

})();
