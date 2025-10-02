/** @deprecated Use collectFormValues */
export function formIsValid(element) {
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

/**
 * Check validity of each element in form or fieldset and collect their values.
 * You may customise the input error message with data-errormessage. If data-errormessage, this
 * function will report that if the input is invalid, instead of the browser's default error message.
 *
 * @param {HTMLFormElement|HTMLFieldSetElement} formLike
 * @param {(string) => string} [nameTransform] Optionnaly transform the collected input's `name` attribute.
 *              Useful when the input is part of a Django formset; this allows you to remove the formset prefix.
 * @return {Object|undefined} Form element values or undefined if form or fieldset is invalid
 */
export function collectFormValues(formLike, {nameTransform, skipValidation} = {
    nameTransform: ((name) => name),
    skipValidation: false
}) {
    const result = {}

    for (const element of formLike.elements) {
        if (!skipValidation) {
            // Clear any previously set custom validity before rechecking
            element.setCustomValidity("")
            if (!element.checkValidity()) {
                if (element.dataset.errormessage) {
                    element.setCustomValidity(element.dataset.errormessage)
                }
                element.reportValidity()
                return undefined
            }
        }


        const inputName = nameTransform(element.name).trim()
        const inputValue = typeof element.value === "string" ? element.value.trim() : ""

        // If form element is a <select> we want to pick the <option> text rather than its value that is purely
        // technical; unless it is managed by Choice.js
        if (element instanceof HTMLSelectElement && element.dataset.choice === undefined && inputValue !== "") {
            const option = element.options[element.selectedIndex]
            result[inputName] = option ? option.innerText.trim() : ""
        }
        else if (element.type === "checkbox") {
            if (element.checked) {
                if (!Array.isArray(result[inputName])) result[inputName] = []
                result[inputName].push(document.querySelector(`label[for="${element.id}"]`).innerText.trim())
            }
        }
        else if (element.type === "radio") {
            if (element.checked) {
                result[inputName] = document.querySelector(`label[for="${element.id}"]`).innerText.trim()
            }
        }
        else {
            result[inputName] = element.value
        }
    }
    return result
}

/** @param {HTMLElement} element */
export function removeRequired(element) {
    element.querySelectorAll('[required], [pattern]').forEach(field => {
        field.required = false
        field.removeAttribute("pattern")
    })
}

export function getSelectedLabel(element) {
    if (!element.value) {
        return null
    }
    return element.options[element.selectedIndex].innerText;
}


export function resetForm(element){
    element.querySelectorAll('input, select, textarea').forEach(field => {
        if (field.type === 'checkbox' || field.type === 'radio') {
            field.checked = false;
        } else {
            field.value = '';
        }
    });
}
