(function() {
    let lieuxCards = []
    let extraFormSaved = 0
    const lieuListElement = document.getElementById("lieux-list")
    const lieuTemplateElement = document.getElementById("lieu-carte")

    function displayLieuxCards() {
        lieuListElement.innerHTML = ""
        if (lieuxCards.length === 0) {
            lieuListElement.innerHTML = "Aucun lieu."
            return
        }

        lieuxCards.forEach(card =>{
            const clone = lieuTemplateElement.cloneNode(true);
            clone.classList.remove('fr-hidden');
            clone.querySelector('.lieu-nom').textContent = card.nom;
            clone.querySelector('.lieu-commune').textContent = card.commune;
            lieuListElement.appendChild(clone);
        })
    }

    document.querySelector("#add-lieu-bouton").addEventListener("click", function(event){
        event.preventDefault()
        const currentModal = document.getElementById("modal-add-lieu-" + extraFormSaved)
        dsfr(currentModal).modal.disclose();
    })

    document.querySelectorAll(".lieu-save-btn").forEach(button => button.addEventListener("click", function(event){
        data = {
            "nom": document.getElementById(`id_lieux-${extraFormSaved}-nom`).value,
            "commune": document.getElementById(`commune-select-${extraFormSaved}`).value
        }
        lieuxCards.push(data)
        displayLieuxCards()
        dsfr(event.target.closest("[id^=modal-add-lieu]")).modal.conceal();
        extraFormSaved++;
    }))

    // TODO EDIter : ouvrir la modale, copier en cas d'annulation, remettre si annluation, et mettre à jour les cartes en identifiant celui qui a été modifié

    // TODO Supprimer : Remettre la modale à zero ? Si on créé et supprime X lieu ça ne marchera plus

})();


// TODO gérer les fermetures du modale (annuler et fermer)
