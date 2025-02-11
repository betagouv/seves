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

function hasStatusToOrganismeNuisibleData() {
    return document.getElementById('status-to-organisme-nuisible-id') !== null;
}

document.addEventListener('DOMContentLoaded', function() {
    if (hasStatusToOrganismeNuisibleData()) {
        setUpOrganismeNuisible();
    }
});
