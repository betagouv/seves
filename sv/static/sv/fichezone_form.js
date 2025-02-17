function initializeChoices(elementId) {
    options = {
        searchResultLimit: 500,
        classNames: {
            containerInner: 'fr-select',
        },
        removeItemButton: true,
        itemSelectText: '',
        noResultsText: 'Aucun résultat trouvé',
        noChoicesText: 'Aucune fiche détection à sélectionner',
        searchFields: ['label'],
    };
    new Choices(document.getElementById(elementId), options);
}

function initializeAllChoices() {
    const totalForms = parseInt(document.getElementById('id_zoneinfestee_set-TOTAL_FORMS').value);
    for (let i = 0; i < totalForms; i++) {
        initializeChoices(`id_zoneinfestee_set-${i}-detections`);
    }
}


function getNextIdToUse(){
    let num = 0
    while (document.getElementById(`id_zoneinfestee_set-${num}-nom`)) {
        num++
    }
    return num
}

function addZoneInfesteeForm() {
    const nextIdToUse = getNextIdToUse()
    let newTabTemplate = document.getElementById('zone-form-template').innerHTML;
    newTabTemplate = newTabTemplate.replace(/__prefix__/g, nextIdToUse.toString());
    document.getElementById('zones-infestees').insertAdjacentHTML('beforeend', newTabTemplate);
    const newDeleteBtn = document.querySelector(`#modal-delete-zi-confirmation-${nextIdToUse} .delete-zone-infestee`)
    newDeleteBtn.addEventListener("click", removeZoneInfesteeForm)
    new Choices(document.getElementById(`id_zoneinfestee_set-${nextIdToUse}-detections`), options);
    updatetotalFormsInput()
}

function updatetotalFormsInput(){
    const totalFormsInput = document.getElementById('id_zoneinfestee_set-TOTAL_FORMS')
    totalFormsInput.value = document.querySelectorAll('[id^="zone-infestee-"]').length
}

function removeZoneInfesteeForm(event){
    const zoneElement = document.getElementById(`zone-infestee-${event.target.dataset.pk}`)
    const isNewZone = zoneElement.dataset.newZone  === "true"
    if (isNewZone) {
        zoneElement.remove()
    } else {
        zoneElement.querySelector('[id^="id_zoneinfestee_set-"][id$="DELETE"]').setAttribute("checked", true)
        zoneElement.classList.add("fr-hidden")
    }

    dsfr(event.target.closest("dialog")).modal.conceal()
    updatetotalFormsInput()
}

document.addEventListener('DOMContentLoaded', function() {

    initializeChoices('id_detections_hors_zone');
    initializeAllChoices();
    const addZoneButton = document.getElementById('add-zone-infestee');
    addZoneButton.addEventListener('click', function(event) {
        event.preventDefault();
        addZoneInfesteeForm();
    });
    document.querySelectorAll("button.delete-zone-infestee").forEach(element => element.addEventListener("click", removeZoneInfesteeForm))

});
