function formIsValid(element) {
    const inputs = element.querySelectorAll("input, textarea, select")
    let isValid = true
    inputs.forEach((input) => {
        if (!input.checkValidity()) {
            input.reportValidity()
            isValid = false
        }
    })
    return isValid
}

function dataRequiredToRequired(element) {
    element.querySelectorAll("[data-required]").forEach((field) => {
        field.required = "true"
    })
}

function removeRequired(element) {
    element.querySelectorAll("[required]").forEach((field) => {
        field.required = false
    })
}

function resetForm(element) {
    element.querySelectorAll("input, select, textarea").forEach((field) => {
        if (field.type === "checkbox" || field.type === "radio") {
            field.checked = false
        } else {
            field.value = ""
        }
    })
}
