document.addEventListener('DOMContentLoaded', function() {
    new Choices(document.getElementById('id_object_choice'), {
        classNames: {
            containerInner: 'fr-select',
        },
        itemSelectText: ''
    });
});
