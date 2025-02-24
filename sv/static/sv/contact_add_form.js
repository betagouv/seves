document.addEventListener('DOMContentLoaded', function() {
    const element = document.getElementById('id_structure');
    const choices = new Choices(element, {
        itemSelectText: '',
        classNames: {
            containerInner: 'fr-select',
        },
        searchResultLimit: 500,
    });
});
