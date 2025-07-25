function setUpOrganismeNuisible(){
    const statusToNuisibleId =  JSON.parse(document.getElementById('status-to-organisme-nuisible-id').textContent)
    const element = document.getElementById('id_organisme_nuisible');
    if(!(element instanceof HTMLElement)) return;
    const choices = new Choices(element, {
        classNames: {
            containerInner: 'fr-select',
        },
        itemSelectText: '',
        position: 'bottom',
        searchResultLimit: 10,
    });

    choices.passedElement.element.addEventListener("choice", (event)=> {
        let found = false;
        const statutElement = document.getElementById('id_statut_reglementaire')
        statusToNuisibleId.forEach((status) =>{
            if (status.nuisibleIds.includes(parseInt(event.detail.value))) {
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
    document.getElementById("cancel-link").addEventListener("click", (event) => {
        event.preventDefault();
        window.location = document.referrer;
    });

    if (hasStatusToOrganismeNuisibleData()) {
        setUpOrganismeNuisible();
    }

});
