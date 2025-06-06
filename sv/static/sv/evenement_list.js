document.addEventListener('DOMContentLoaded', function() {
    const choicesOrganismeNuisible = new Choices(document.getElementById('id_organisme_nuisible'), {
        classNames: {
            containerInner: 'fr-select',
        },
        itemSelectText: ''
    });

    const choicesAgentContact = new Choices(document.getElementById('id_agent_contact'), {
        classNames: {
            containerInner: 'fr-select',
        },
        itemSelectText: ''
    });

    document.getElementById('search-form').addEventListener('reset', function (e) {
        e.preventDefault();
        this.elements['numero'].value = '';
        this.elements['region'].value = '';
        this.elements['organisme_nuisible'].value = '';
        this.elements['start_date'].value = '';
        this.elements['end_date'].value = '';
        this.elements['etat'].value = '';
        choicesOrganismeNuisible.setChoiceByValue('');
        this.elements['structure_contact'].value = '';
        choicesAgentContact.setChoiceByValue('');
        e.target.closest("form").submit();
    });

});
