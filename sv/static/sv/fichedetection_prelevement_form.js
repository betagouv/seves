let prelevementCards =[]
let extraFormSaved = 0

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


function deletePrelevement(event) {
    const id = event.target.dataset.id
    prelevementCards = prelevementCards.filter(function(item) {return item.id !== id})
    // TODO empty form or do something ?  : : todo we need and empty template to do this
    displayPrelevementsCards()
    dsfr(document.getElementById('modal-delete-prelevement-confirmation')).modal.conceal();
}

function displayPrelevementsCards() {
    const prelevementListElement = document.getElementById("prelevements-list")
    const prelevementTemplateElement = document.getElementById("prelevement-carte")
    prelevementListElement.innerHTML = ""
    prelevementCards.forEach(card =>{
        const clone = prelevementTemplateElement.cloneNode(true);
        clone.classList.remove('fr-hidden');
        clone.querySelector('.prelevement-nom').textContent = card.structure;
        clone.querySelector('.prelevement-lieu').textContent = "Lieu : " + card.lieu;
        clone.querySelector('.prelevement-type').textContent = `${card.officiel} | ${card.detecte}`;
        clone.querySelector('.prelevement-delete-btn').setAttribute("data-id", card.id)
        // TODO add edit btn
            // clone.querySelector('.lieu-edit-btn').addEventListener("click", (event)=>{
            //     dsfr(document.getElementById("modal-add-lieu-" + card.id)).modal.disclose()
            // })
        clone.querySelector('.prelevement-delete-btn').addEventListener("click", (event)=>{
            dsfr(document.getElementById("modal-delete-prelevement-confirmation")).modal.disclose()
            document.getElementById("delete-prelevement-confirm-btn").setAttribute("data-id", event.target.dataset.id)
        })
        prelevementListElement.appendChild(clone);
    })
    showOrHidePrelevementUI()
}

function addPrelevementmodal(event) {
    event.preventDefault()
    const currentModal = document.getElementById("modal-add-edit-prelevement-" + extraFormSaved)
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
}

(function() {


    showOrHidePrelevementUI()
    document.getElementById("btn-add-prelevment").addEventListener("click", addPrelevementmodal)
    document.getElementById("delete-prelevement-confirm-btn").addEventListener("click", deletePrelevement)

    document.querySelectorAll(".prelevement-save-btn").forEach(button => button.addEventListener("click", function(event){
        const id = event.target.dataset.id
        const modal = document.getElementById(`modal-add-edit-prelevement-${id}`)
        const isValid = formIsValid(modal)
        if (isValid === false){
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

        const index = prelevementCards.findIndex(element => element.id === data.id);
        if (index === -1) {
            prelevementCards.push(data);
            extraFormSaved++;
        } else {
            prelevementCards[index] = data;
        }

        displayPrelevementsCards()
        modal.querySelectorAll('input, textarea, select').forEach((input) =>{
            if (input.hasAttribute("required")){
                input.required = false
            }
        })
        dsfr(modal).modal.conceal();
    }))


})();

// TODO retirer le required dans le form lors de la fermeture de la modale
// TODO remettre les required dans les form à l'ouverture de la modale
