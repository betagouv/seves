document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('search-form').addEventListener('reset', function (e) {
        e.preventDefault();
        this.elements['numero'].value = '';
        this.elements['lieux__departement__region'].value = '';
        this.elements['organisme_nuisible'].value = '';
        this.elements['start_date'].value = '';
        this.elements['end_date'].value = '';
        this.elements['etat'].value = '';
    });

    const choices = new Choices(document.getElementById('id_organisme_nuisible'), {
        classNames: {
            containerInner: 'fr-select',
        },
        itemSelectText: ''
    });
});
