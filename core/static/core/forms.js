// biome-ignore lint/correctness/noUnusedVariables: used dynamically
function formIsValid(element) {
    const inputs = element.querySelectorAll("input, textarea, select")
    let isValid = true
    inputs.forEach(input => {
        if (!input.checkValidity()) {
            input.reportValidity()
            isValid = false
        }
    })
    return isValid
}

// biome-ignore lint/correctness/noUnusedVariables: used dynamically
function dataRequiredToRequired(element) {
    element.querySelectorAll("[data-required]").forEach(field => {
        field.required = "true"
    })
}

// biome-ignore lint/correctness/noUnusedVariables: used dynamically
function removeRequired(element) {
    element.querySelectorAll("[required]").forEach(field => {
        field.required = false
    })
}

// biome-ignore lint/correctness/noUnusedVariables: used dynamically
function resetForm(element) {
    element.querySelectorAll("input, select, textarea").forEach(field => {
        if (field.type === "checkbox" || field.type === "radio") {
            field.checked = false
        } else {
            field.value = ""
        }
    })
}
