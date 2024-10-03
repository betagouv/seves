document.addEventListener('DOMContentLoaded', function() {
/*
    const element = document.getElementById('id_detections_hors_zone_infestee');
    const choices = new Choices(element, {
        searchResultLimit: 500,
        classNames: {
            containerInner: 'fr-select',
        },
        removeItemButton: true,
        itemSelectText: '',
        noResultsText: 'Aucun résultat trouvé',
        noChoicesText: 'Aucune fiche détection à sélectionner',
    });
*/
    const addZoneButton = document.getElementById('add-zone-infestee');
    addZoneButton.addEventListener('click', function(event) {
        event.preventDefault();

        const totalFormsInput = document.getElementById('id_zoneinfestee_set-TOTAL_FORMS');
        let totalForms = parseInt(totalFormsInput.value);

        let newTabTemplate = document.getElementById('zone-form-template').innerHTML;
        newTabTemplate = newTabTemplate.replace(/__prefix__/g, totalForms);
        document.getElementById('zones-infestees').insertAdjacentHTML('beforeend', newTabTemplate);

        totalFormsInput.value = totalForms+1;
    });

});
