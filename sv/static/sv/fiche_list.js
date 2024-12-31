document.addEventListener('DOMContentLoaded', function() {
    const choices = new Choices(document.getElementById('id_evenement__organisme_nuisible'), {
        classNames: {
            containerInner: 'fr-select',
        },
        itemSelectText: ''
    });

    document.getElementById('search-form').addEventListener('reset', function (e) {
        e.preventDefault();
        this.elements['numero'].value = '';
        this.elements['lieux__departement__region'].value = '';
        this.elements['organisme_nuisible'].value = '';
        this.elements['start_date'].value = '';
        this.elements['end_date'].value = '';
        this.elements['etat'].value = '';
        choices.setChoiceByValue('');
    });
    document.getElementById("id_type_fiche_0").addEventListener("click", event =>{
        document.getElementById('id_lieux__departement__region').disabled = false
    })
    document.getElementById("id_type_fiche_1").addEventListener("click", event =>{
        document.getElementById('id_lieux__departement__region').disabled = true
        document.getElementById('id_lieux__departement__region').selectedIndex = 0
    })
    if (new URLSearchParams(window.location.search).get('type_fiche') === "zone"){
        document.getElementById('id_lieux__departement__region').disabled = true
        document.getElementById('id_lieux__departement__region').selectedIndex = 0
    }
});
