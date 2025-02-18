function handleTypeFicheChange(event, disableRegion) {
    const numeroInput = document.getElementById('id_numero');
    if (numeroInput.value) {
        if (!numeroInput.checkValidity()) {
            event.preventDefault();
            numeroInput.reportValidity();
            return;
        }
        numeroInput.value = '';
    }
    const regionSelect = document.getElementById('id_lieux__departement__region');
    regionSelect.disabled = disableRegion;
    if (disableRegion) {
        regionSelect.selectedIndex = 0;
    }
    event.target.closest("form").submit();
}

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
        this.elements['evenement__organisme_nuisible'].value = '';
        this.elements['start_date'].value = '';
        this.elements['end_date'].value = '';
        this.elements['evenement__etat'].value = '';
        choices.setChoiceByValue('');
        e.target.closest("form").submit();
    });

    document.getElementById("id_type_fiche_0").addEventListener("click", e => handleTypeFicheChange(e, false));
    document.getElementById("id_type_fiche_1").addEventListener("click", e => handleTypeFicheChange(e, true));

    if (new URLSearchParams(window.location.search).get('type_fiche') === "zone") {
        document.getElementById('id_lieux__departement__region').disabled = true;
        document.getElementById('id_lieux__departement__region').selectedIndex = 0;
    }

});
