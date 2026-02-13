import {
    validateFileSize,
    updateAcceptAttributeFileInput,
    getAcceptAllowedExtensionsAttributeValue,
    isSelectedFileExtensionValid,
    removeEmptyOptionIfExist,
} from "./document.js"

document.addEventListener("DOMContentLoaded", () => {
    const uploadModal = document.getElementById("fr-modal-add-doc")
    if (!uploadModal) return

    const fileInput = uploadModal.querySelector('input[type="file"]')
    const documentTypeSelect = uploadModal.querySelector('select[name="document_type"]')
    const submitButton = uploadModal.querySelector('button[type="submit"]')
    const extensionsInfoSpan = uploadModal.querySelector("#allowed-extensions-list")

    fileInput.addEventListener("change", () => onFileInputChange(fileInput, documentTypeSelect))
    documentTypeSelect.addEventListener("change", () =>
        onDocumentTypeChange(fileInput, documentTypeSelect, extensionsInfoSpan, submitButton),
    )
    submitButton.addEventListener("click", (event) => onFormSubmit(event, fileInput, documentTypeSelect))
})

function onFileInputChange(fileInput, documentTypeSelect) {
    if (!validateFileSize(fileInput)) {
        return
    }
    const documentTypeAllowedExtensions = getAcceptAllowedExtensionsAttributeValue(fileInput, documentTypeSelect)
    isSelectedFileExtensionValid(fileInput, documentTypeAllowedExtensions)
}

function onDocumentTypeChange(fileInput, documentTypeSelect, extensionsInfoSpan, submitButton) {
    const documentTypeAllowedExtensions = getAcceptAllowedExtensionsAttributeValue(fileInput, documentTypeSelect)
    if (documentTypeAllowedExtensions === null) {
        submitButton.setAttribute("disabled", "true")
        return
    }
    removeEmptyOptionIfExist(documentTypeSelect)
    fileInput.removeAttribute("disabled")
    submitButton.removeAttribute("disabled")
    updateAcceptAttributeFileInput(fileInput, documentTypeSelect, documentTypeAllowedExtensions, extensionsInfoSpan)
    isSelectedFileExtensionValid(fileInput, documentTypeAllowedExtensions)
}

function onFormSubmit(event, fileInput, documentTypeSelect) {
    event.preventDefault()
    const form = event.target.closest("form")
    if (!validateFileSize(fileInput)) {
        return
    }
    const documentTypeAllowedExtensions = getAcceptAllowedExtensionsAttributeValue(fileInput, documentTypeSelect)
    if (documentTypeAllowedExtensions === null) {
        return
    }
    isSelectedFileExtensionValid(fileInput, documentTypeAllowedExtensions)
    if (!form.checkValidity()) {
        form.reportValidity()
        return
    }
    form.submit()
}
