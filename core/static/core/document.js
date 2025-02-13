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
