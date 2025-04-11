document.documentElement.addEventListener('dsfr.ready', () => {
    function disableSourceOptions(typeEvenementInput, sourceInput) {
        const isHumanCase = typeEvenementInput.value === "investigation_cas_humain";
        sourceInput.querySelectorAll('option').forEach(option => {
            if (option.value !== "autre") {
                option.disabled = (option.getAttribute('data-for-human-case') === 'true') !== isHumanCase;
            }
        });
        sourceInput.selectedIndex = 0;
    }

    const typeEvenementInput = document.getElementById('id_type_evenement')
    const sourceInput = document.getElementById('id_source')
    typeEvenementInput.addEventListener("change", () => {
        disableSourceOptions(typeEvenementInput, sourceInput)
    })
    disableSourceOptions(typeEvenementInput, sourceInput)
});
