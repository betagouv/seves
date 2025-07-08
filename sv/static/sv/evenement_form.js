import choicesDefaults from "choicesDefaults"
import {setUpFreeLinks} from "/static/core/free_links.js";

function setUpOrganismeNuisible(){
    const statusToNuisibleId =  JSON.parse(document.getElementById('status-to-organisme-nuisible-id').textContent)
    const element = document.getElementById('id_organisme_nuisible');
    const choices = new Choices(element, choicesDefaults);

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

document.addEventListener('DOMContentLoaded', function() {
    setUpOrganismeNuisible()
    setUpFreeLinks(document.getElementById("id_free_link"), document.getElementById('free-links-id'))
});
