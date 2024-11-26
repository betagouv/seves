function setUpOrganismeNuisible(){
    const statusToNuisibleId =  JSON.parse(document.getElementById('status-to-organisme-nuisible-id').textContent)
    const element = document.getElementById('id_organisme_nuisible');
    const choices = new Choices(element, {
        classNames: {
            containerInner: 'fr-select',
        },
        itemSelectText: ''
    });

    choices.passedElement.element.addEventListener("choice", (event)=> {
        let found = false;
        const statutElement = document.getElementById('id_statut_reglementaire')
        statusToNuisibleId.forEach((status) =>{
            if (status.nuisibleIds.includes(parseInt(event.detail.choice.value))) {
                statutElement.value = status.statusID;
                statutElement.dispatchEvent(new Event('change'));
                found = true;
            }
        })
        if (found === false){
            statutElement.value="";
            statutElement.dispatchEvent(new Event('change'));
        }
    })

}

function setUpFreeLinks(){
    const freeLinksChoices = new Choices(document.getElementById("id_free_link"), {
        searchResultLimit: 500,
        classNames: {
            containerInner: 'fr-select',
        },
        removeItemButton: true,
        shouldSort: false,
        itemSelectText: '',
        noResultsText: 'Aucun résultat trouvé',
        noChoicesText: 'Aucune fiche à sélectionner',
        searchFields: ['label'],
    });
    const freeLinksIds = JSON.parse(document.getElementById('free-links-id').textContent);
    if (!!freeLinksIds) {
        freeLinksIds.forEach(value => {
            freeLinksChoices.setChoiceByValue(value);
        });
    }
}

document.addEventListener('DOMContentLoaded', function() {
    setUpOrganismeNuisible()
    setUpFreeLinks()
});
