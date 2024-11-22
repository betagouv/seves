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
            clone.querySelector('.lieu-edit-btn').addEventListener("click", (event)=>{
                dsfr(document.getElementById("modal-add-lieu-" + card.id)).modal.disclose()
            })
            lieuListElement.appendChild(clone);
        })
    }

    document.querySelector("#add-lieu-bouton").addEventListener("click", function(event){
        event.preventDefault()
        const currentModal = document.getElementById("modal-add-lieu-" + extraFormSaved)
        dsfr(currentModal).modal.disclose();
    })

    document.querySelectorAll(".lieu-save-btn").forEach(button => button.addEventListener("click", function(event){
        const id = event.target.dataset.id
        let data = {
            "id": id,
            "nom": document.getElementById(`id_lieux-${id}-nom`).value,
            "commune": document.getElementById(`commune-select-${id}`).value
        }

        const index = lieuxCards.findIndex(element => element.id === data.id);
        if (index === -1) {
            lieuxCards.push(data);
            extraFormSaved++;
        } else {
            lieuxCards[index] = data;
        }

        displayLieuxCards()
        dsfr(event.target.closest("[id^=modal-add-lieu]")).modal.conceal();

    }))

    // TODO EDIter : ouvrir la modale, copier en cas d'annulation, remettre si annulation

    // TODO Supprimer : Remettre la modale à zero ? Si on créé et supprime X lieu ça ne marchera plus

})();


// TODO gérer les fermetures du modale (annuler et fermer)
