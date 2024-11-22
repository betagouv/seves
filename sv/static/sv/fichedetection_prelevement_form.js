function showOrHidePrelevementUI(){
    const nbLieux = document.getElementById("lieux-list").childElementCount

    if (nbLieux === 0){
        document.getElementById("no-lieux-text").classList.remove("fr-hidden")
        document.getElementById("btn-add-prelevment").disabled = true

    } else {
        document.getElementById("no-lieux-text").classList.add("fr-hidden")
        document.getElementById("btn-add-prelevment").disabled = false
    }
}

function displayPrelevementsCards(prelevementCards) {
    const prelevementListElement = document.getElementById("prelevements-list")
    const prelevementTemplateElement = document.getElementById("prelevement-carte")
    prelevementListElement.innerHTML = ""
        // if (prelevementCards.length === 0) {
        //     // TODO adapt this
        //     lieuListElement.innerHTML = "Aucun lieu."
        //     return
        // }

    prelevementCards.forEach(card =>{
        const clone = prelevementTemplateElement.cloneNode(true);
        clone.classList.remove('fr-hidden');
        clone.querySelector('.prelevement-nom').textContent = card.structure;
            // clone.querySelector('.lieu-commune').textContent = card.commune;
            // clone.querySelector('.lieu-edit-btn').addEventListener("click", (event)=>{
            //     dsfr(document.getElementById("modal-add-lieu-" + card.id)).modal.disclose()
            // })
        prelevementListElement.appendChild(clone);
    })
    showOrHidePrelevementUI()
}

(function() {
    let extraFormSaved = 0
    let prelevementCards =[]

    showOrHidePrelevementUI()


    document.getElementById("btn-add-prelevment").addEventListener("click", (event)=>{
        event.preventDefault()
        const currentModal = document.getElementById("modal-add-edit-prelevement-" + extraFormSaved)
        dsfr(currentModal).modal.disclose();
    })

    document.querySelectorAll(".prelevement-save-btn").forEach(button => button.addEventListener("click", function(event){
        const id = event.target.dataset.id
        const modal = document.getElementById(`modal-add-edit-prelevement-${id}`)
        // TODO factorize this
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

        // TODO fill all this
        const structureElement = document.getElementById(`id_prelevements-${id}-structure_preleveur`)
        let data = {
            "id": id,
            "structure":structureElement.options[structureElement.selectedIndex].text,
            "lieu": "",
            "officiel": "",
            "detecte": "",
        }

        const index = prelevementCards.findIndex(element => element.id === data.id);
        if (index === -1) {
            prelevementCards.push(data);
            extraFormSaved++;
        } else {
            prelevementCards[index] = data;
        }

        displayPrelevementsCards(prelevementCards)
        dsfr(modal).modal.conceal();
    }))


})();
