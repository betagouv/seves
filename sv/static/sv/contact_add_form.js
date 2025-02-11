document.addEventListener('DOMContentLoaded', function() {
    const element = document.getElementById('id_structure');
    const choices = new Choices(element, {
        itemSelectText: '',
        classNames: {
            containerInner: 'fr-select fr-mt-1w',
        },
        searchResultLimit: 500,
    });
});
