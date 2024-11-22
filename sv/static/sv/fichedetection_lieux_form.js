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

    function showLieuDetailsIfIsEtablissement(){
        const elements = document.querySelectorAll('[id^="id_lieux-"][id$="-is_etablissement"]');
        elements.forEach((element) => element.addEventListener("change", (event) =>{
            event.target.closest("p").nextElementSibling.classList.toggle("fr-hidden")
        })
        )}


    document.querySelector("#add-lieu-bouton").addEventListener("click", function(event){
        event.preventDefault()
        const currentModal = document.getElementById("modal-add-lieu-" + extraFormSaved)
        dsfr(currentModal).modal.disclose();
    })

    document.querySelectorAll(".lieu-save-btn").forEach(button => button.addEventListener("click", function(event){
        const id = event.target.dataset.id
        const modal = document.getElementById(`modal-add-lieu-${id}`)

        const inputs = modal.querySelectorAll('input, textarea, select');
        let isValid = true;
        inputs.forEach(input => {
            if (!input.checkValidity()) {
                input.reportValidity();
                isValid = false;
            }
        });
        if (isValid === false){
            return
        }

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


    showLieuDetailsIfIsEtablissement();

    // TODO EDIter : ouvrir la modale, copier en cas d'annulation, remettre si annulation

    // TODO Supprimer : Remettre la modale à zero ? Si on créé et supprime X lieu ça ne marchera plus :possibilité d'avoir une listes des ids déjàs utilisés

})();


// TODO gérer les fermetures du modale (annuler et fermer)
