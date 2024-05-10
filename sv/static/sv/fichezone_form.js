document.addEventListener('DOMContentLoaded', function() {

    const addZoneButton = document.getElementById('add-zone');

    addZoneButton.addEventListener('click', function() {

        event.preventDefault();

        const totalFormsInput = document.getElementById('id_form-TOTAL_FORMS');
        let totalForms = parseInt(totalFormsInput.value);

	// Btn de l'onglet
        let newTabTemplate = document.getElementById('zone-form-tabs-btn').innerHTML;
        newTabTemplate = newTabTemplate.replace(/__prefix__/g, totalForms);
        newTabTemplate = newTabTemplate.replace(/__zone_nb__/g, totalForms+1);
        document.querySelector('.fr-tabs__list').insertAdjacentHTML('beforeend', newTabTemplate);

	// Contenu de l'onglet
        var templateElement = document.getElementById('zone-form-tabs-content');
        let newPanelTemplate = templateElement.innerHTML;
        newPanelTemplate = newPanelTemplate.replace(/__prefix__/g, totalForms);
        document.querySelector('.fr-tabs').insertAdjacentHTML('beforeend', newPanelTemplate);

        totalFormsInput.value = totalForms+1;

	// focus sur le nouvel onglet
	//const newTabPanel = document.getElementById(`tabpanel-${totalForms}-panel`);
	//window.dsfr(newTabPanel).tabPanel.focus();
    });

});
