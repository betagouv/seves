document.addEventListener('DOMContentLoaded', function() {
    const options = {
        itemSelectText: '',
        classNames: {
            containerInner: 'fr-select',
        },
        removeItemButton: true,
    }
    const select_contacts_structures = document.getElementById('id_contacts_structures');
    const select_contacts_agents = document.getElementById('id_contacts_agents');
    new Choices(select_contacts_structures, options);
    new Choices(select_contacts_agents, options);
});
