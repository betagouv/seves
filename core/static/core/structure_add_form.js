document.addEventListener('DOMContentLoaded', function() {
    const form = document.querySelector('#structures-form');
    const checkboxes = form.querySelectorAll('input[type=checkbox]');

    function init() {
        form.addEventListener('submit', validateForm);
        checkboxes.forEach(checkbox => checkbox.addEventListener('change', clearError));
    }

    function validateForm(event) {
        if (!Array.from(checkboxes).some(checkbox => checkbox.checked)) {
            event.preventDefault();
            checkboxes[0].setCustomValidity('Vous devez choisir au moins une structure.');
            checkboxes[0].reportValidity()
        }
    }

    function clearError() {
        if (Array.from(checkboxes).some(checkbox => checkbox.checked)) {
            checkboxes[0].setCustomValidity('')
        }
    }

    init()
})
