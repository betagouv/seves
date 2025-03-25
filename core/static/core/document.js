export function validateFileSize(fileInput) {
    const maxSizeAttr = fileInput.getAttribute('data-max-size');

    if (maxSizeAttr === null) {
        console.error("Erreur de configuration: l'attribut 'data-max-size' est manquant");
        fileInput.setCustomValidity("Erreur de configuration: limite de taille non définie");
        fileInput.reportValidity();
        return false;
    }

    const maxSizeBytes = parseInt(maxSizeAttr);
    if (isNaN(maxSizeBytes)) {
        console.error("Erreur de configuration: 'data-max-size' n'est pas un nombre valide");
        fileInput.setCustomValidity("Erreur de configuration: limite de taille invalide");
        fileInput.reportValidity();
        return false;
    }

    if (fileInput.files[0] && fileInput.files[0].size > maxSizeBytes) {
        const maxSizeMB = maxSizeBytes / (1024 * 1024);
        fileInput.setCustomValidity(`Le fichier est trop volumineux (maximum ${maxSizeMB} Mo autorisés)`);
        fileInput.reportValidity();
        return false;
    }

    fileInput.setCustomValidity('');
    return true;
}

export function getAcceptAllowedExtensionsAttributeValue(fileInput, documentTypeSelect) {
    const attributeName = "data-accept-allowed-extensions";
    const acceptAllowedExtensionsAttributeJson = fileInput.getAttribute(attributeName);

    if (acceptAllowedExtensionsAttributeJson === null) {
        console.error(`Erreur de configuration: l'attribut '${attributeName}' est manquant`);
        fileInput.setCustomValidity("Erreur de configuration: extensions autorisées non définies");
        fileInput.reportValidity();
        return null;
    }

    let allowedExtensions;
    try {
        allowedExtensions = JSON.parse(acceptAllowedExtensionsAttributeJson);
    } catch (error) {
        console.error(`Erreur de configuration: l'attribut '${attributeName}' contient un JSON invalide`, error);
        fileInput.setCustomValidity("Erreur de configuration: format des extensions autorisées invalide");
        fileInput.reportValidity();
        return null;
    }

    const currentDocumentType = documentTypeSelect.value;
    const extensionsToUse = allowedExtensions[currentDocumentType];
    if (!extensionsToUse) {
        console.error(`Erreur de configuration: aucune extension définie dans l'attribut '${attributeName}' pour le type '${currentDocumentType}' ou pas de valeur par défaut`);
        fileInput.setCustomValidity(`Erreur de configuration: aucune extension définie pour ce type de document`);
        fileInput.reportValidity();
        fileInput.setAttribute('accept', "");
        return null;
    }

    return extensionsToUse;
}

function validateSelectedFileExtension(fileInput, extensionsToUse) {
    fileInput.setCustomValidity('');

    if (!fileInput.files || fileInput.files.length === 0) {
        return;
    }

    // Extraire l'extension du fichier
    const fileName = fileInput.files[0].name;
    const fileExtension = fileName.lastIndexOf('.') !== -1 ? fileName.slice(fileName.lastIndexOf('.') + 1).toLowerCase() : '';
    if (!fileExtension) {
        fileInput.setCustomValidity("Le fichier sélectionné n'a pas d'extension");
        fileInput.reportValidity();
        return;
    }

    // Normaliser les extensions autorisées
    const allowedExtensions = extensionsToUse.split(',').map(ext => ext.replace(/^\./, ''));

    // Vérifier si l'extension est autorisée
    if (!allowedExtensions.includes(fileExtension)) {
        fileInput.setCustomValidity(`Le fichier sélectionné ne correspond pas au type de document (extensions autorisées : ${allowedExtensions.join(', ')})`);
        fileInput.reportValidity();
    }
}

export function updateFileConstraintsAndValidate(fileInput, documentTypeSelect) {
    // Récupère les extensions autorisées pour tous les types de documents
    const extensionsToUse = getAcceptAllowedExtensionsAttributeValue(fileInput, documentTypeSelect);
    if (extensionsToUse === null) {
        return;
    }

    // MAJ de l'attribut accept et de l'affichage des extensions autorisées
    fileInput.setAttribute('accept', extensionsToUse);
    const extensionsInfoSpan = document.getElementById("allowed-extensions-list");
    extensionsInfoSpan.textContent = extensionsToUse.split(',').map(ext => ext.replace('.', '')).join(', ');

    validateSelectedFileExtension(fileInput, extensionsToUse);
}
