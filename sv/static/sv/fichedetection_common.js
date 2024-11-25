function formIsValid(element){
    const inputs = element.querySelectorAll('input, textarea, select');
    let isValid = true;
    inputs.forEach(input => {
        if (!input.checkValidity()) {
            input.reportValidity();
            isValid = false;
        }
    });
    return isValid
}

function dataRequiredToRequired(element){
    element.querySelectorAll('[data-required]').forEach(field =>{
        field.required = "true"
    })
}

// TODO il faut faire ça à la sauvegarde mais aussi à chaque fois que la modale est cachée mais non sauvegarder
// TODO idem a ce moment il faut vider tous les champs ?
function removeRequired(element){
    element.querySelectorAll('[required]').forEach(field =>{
        field.required = ""
    })
}

function resetForm(element){
    element.querySelectorAll('input, select, textarea').forEach(field => {
        if (field.type === 'checkbox' || field.type === 'radio') {
            field.checked = false;
        } else {
            field.value = '';
        }
    });
}
