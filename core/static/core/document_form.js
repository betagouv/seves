import { validateFileSize, updateFileConstraintsAndValidate, getAcceptAllowedExtensionsAttributeValue }  from './document.js';

document.addEventListener('DOMContentLoaded', () => {
    const uploadModal = document.getElementById('fr-modal-add-doc');
    if (!uploadModal) return;

    const fileInput = uploadModal.querySelector('input[type="file"]');
    const documentTypeSelect = uploadModal.querySelector('select[name="document_type"]');
    const submitButton = uploadModal.querySelector('button[type="submit"]');

    fileInput.addEventListener('change', () => handleFileInputChange(fileInput, documentTypeSelect));
    documentTypeSelect.addEventListener('change', (event) => updateFileConstraintsAndValidate(fileInput, documentTypeSelect));
    submitButton.addEventListener("click", (event) => handleFormSubmit(event, fileInput, documentTypeSelect));
});

function handleFileInputChange(fileInput, documentTypeSelect) {
    validateFileSize(fileInput);
    getAcceptAllowedExtensionsAttributeValue(fileInput, documentTypeSelect);
}

function handleFormSubmit(event, fileInput, documentTypeSelect) {
    // Vérification des extensions autorisées avant de soumettre le formulaire
    // car si pas de selection du type de document, l'attribut accept n'est pas mis à jour
    // et donc pas de vérification effectuée via getAcceptAllowedExtensionsAttributeValue
    if (getAcceptAllowedExtensionsAttributeValue(fileInput, documentTypeSelect) === null) {
        event.preventDefault();
    }
}
