export function formIsValid(element){
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

export function removeRequired(element){
    element.querySelectorAll('[required]').forEach(field =>{
        field.required = false
    })
}

export function getSelectedLabel(element) {
    if (!element.value) {
        return null
    }
    return element.options[element.selectedIndex].innerText;
}
