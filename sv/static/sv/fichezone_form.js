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

function inititializeFreeLinksChoices(){
    const freeLinksChoices = new Choices(document.getElementById("id_free_link"), {
        searchResultLimit: 500,
        classNames: {
            containerInner: 'fr-select',
        },
        removeItemButton: true,
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

function addZoneInfesteeForm() {
    const totalFormsInput = document.getElementById('id_zoneinfestee_set-TOTAL_FORMS');
    let totalForms = parseInt(totalFormsInput.value);

    let newTabTemplate = document.getElementById('zone-form-template').innerHTML;
    newTabTemplate = newTabTemplate.replace(/__prefix__/g, totalForms);
    document.getElementById('zones-infestees').insertAdjacentHTML('beforeend', newTabTemplate);

    new Choices(document.getElementById(`id_zoneinfestee_set-${totalForms}-detections`), options);

    totalFormsInput.value = totalForms+1;
}

document.addEventListener('DOMContentLoaded', function() {

    initializeChoices('id_detections_hors_zone');
    initializeAllChoices();
    inititializeFreeLinksChoices();
    const addZoneButton = document.getElementById('add-zone-infestee');
    addZoneButton.addEventListener('click', function(event) {
        event.preventDefault();
        addZoneInfesteeForm();
    });

});
