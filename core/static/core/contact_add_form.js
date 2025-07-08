import choicesDefaults from "choicesDefaults"

document.addEventListener('DOMContentLoaded', function() {
    const options = {
        ...choicesDefaults,
        removeItemButton: true,
        placeholderValue: "Choisir dans la liste",
        searchPlaceholderValue: "Choisir dans la liste",
        noChoicesText: 'Aucune fiche à sélectionner',
    };
    const select_contacts_structures = document.getElementById('id_contacts_structures');
    const select_contacts_agents = document.getElementById('id_contacts_agents');

    select_contacts_structures.style.visibility = 'visible';
    select_contacts_agents.style.visibility = 'visible';

    new Choices(select_contacts_structures, options);
    new Choices(select_contacts_agents, options);
});
