/** @deprecated Use collectFormValues */
export function formIsValid(element) {
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
export function collectFormValues(
    formLike,
    {nameTransform, skipValidation} = {
        nameTransform: name => name,
        skipValidation: false,
    },
) {
    const result = {}

    for (const element of formLike.elements) {
        if (element instanceof HTMLFieldSetElement || element instanceof HTMLButtonElement) {
            continue
        }

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

        if (inputName === "") continue

        if (element instanceof HTMLSelectElement && element.dataset.choice !== undefined) {
            // This is a ChoiceJS. We process them differently here. We may want both the value and the label
            // Maybe refactor this in the future so that we do that also for normal HTMLSelectElement to minimize code?
            if (element.multiple && !Array.isArray(result[inputName])) {
                result[inputName] = []
                result[`${inputName}Label`] = []
            } else {
                result[inputName] = ""
                result[`${inputName}Label`] = ""
            }

            try {
                if (element.multiple) {
                    for (const option of element.selectedOptions) {
                        result[`${inputName}Label`].push(option.innerText.trim())
                        result[inputName].push(option.value)
                    }
                } else {
                    result[`${inputName}Label`] = element.selectedOptions[0].innerText.trim()
                    result[inputName] = element.selectedOptions[0].value
                }
            } catch (_) {}
        } else if (element instanceof HTMLSelectElement) {
            if (element.multiple && !Array.isArray(result[inputName])) {
                result[inputName] = []
            } else {
                result[inputName] = ""
            }

            try {
                if (element.multiple) {
                    for (const option of element.selectedOptions) {
                        result[inputName].push(option.innerText.trim())
                    }
                } else {
                    result[inputName] = element.selectedOptions[0].innerText.trim()
                }
            } catch (_) {}
        } else if (element.type === "checkbox") {
            if (!Array.isArray(result[inputName])) {
                result[inputName] = []
            }
            if (element.checked) {
                try {
                    result[inputName].push(element.labels[0].textContent.trim())
                } catch (_) {}
            }
        } else if (element.type === "radio") {
            if (!Object.hasOwn(result, inputName)) {
                result[inputName] = ""
            }
            if (element.checked) {
                try {
                    result[inputName] = element.labels[0].textContent.trim()
                } catch (_) {}
            }
        } else {
            result[inputName] = element.value
        }
    }
    return result
}

/** @param {HTMLElement} element */
export function removeRequired(element) {
    element.querySelectorAll("[required], [pattern]").forEach(field => {
        field.required = false
    })
}

export function getSelectedLabel(element) {
    if (!element.value) {
        return null
    }
    return element.options[element.selectedIndex].innerText
}

export function resetForm(element) {
    element.querySelectorAll("input, select, textarea").forEach(field => {
        if (field.type === "checkbox" || field.type === "radio") {
            if (field.checked) {
                field.checked = false
                field.dispatchEvent(new Event("change"))
            }
        } else {
            field.value = ""
        }
    })
}

export function restoreFormValues(fieldset, initialValues) {
    for (const [name, value] of Object.entries(initialValues)) {
        const elements = fieldset.querySelectorAll(`[name="${name}"]`)

        for (const el of elements) {
            if (el.type === "checkbox") {
                if (Array.isArray(value)) {
                    el.checked = value.includes(el.labels?.[0]?.textContent?.trim())
                } else {
                    el.checked = false
                }
            } else if (el.type === "radio") {
                el.checked = el.labels?.[0]?.textContent?.trim() === value
            } else if (el instanceof HTMLSelectElement) {
                for (const option of el.options) {
                    if (Array.isArray(value)) {
                        option.selected = value.includes(option.textContent.trim())
                    } else {
                        option.selected = option.textContent.trim() === value
                    }
                }
            } else {
                el.value = value ?? ""
            }
        }
    }
}

export function resetChoiceJsValue(choice, initialValues, key) {
    const labelKey = Object.keys(initialValues).find(k => k.endsWith(`${key}Label`))
    const valueKey = Object.keys(initialValues).find(k => k.endsWith(key))
    choice.setValue([{value: initialValues[valueKey], label: initialValues[labelKey]}])
    choice.setChoiceByValue(initialValues[valueKey])
}
