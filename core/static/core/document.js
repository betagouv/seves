export function validateFileSize(fileInput) {
    const maxSizeAttr = fileInput.getAttribute("data-max-size")

    if (maxSizeAttr === null) {
        console.error("Erreur de configuration: l'attribut 'data-max-size' est manquant")
        fileInput.setCustomValidity("Erreur de configuration: limite de taille non définie")
        fileInput.reportValidity()
        return false
    }

    const maxSizeBytes = parseInt(maxSizeAttr)
    if (isNaN(maxSizeBytes)) {
        console.error("Erreur de configuration: 'data-max-size' n'est pas un nombre valide")
        fileInput.setCustomValidity("Erreur de configuration: limite de taille invalide")
        fileInput.reportValidity()
        return false
    }

    if (fileInput.files[0] && fileInput.files[0].size > maxSizeBytes) {
        const maxSizeMB = maxSizeBytes / (1024 * 1024)
        fileInput.setCustomValidity(`Le fichier est trop volumineux (maximum ${maxSizeMB} Mo autorisés)`)
        fileInput.reportValidity()
        return false
    }

    fileInput.setCustomValidity("")
    return true
}

export function getAcceptAllowedExtensionsAttributeValue(fileInput, documentTypeSelect) {
    const attributeName = "data-accept-allowed-extensions"
    const acceptAllowedExtensionsAttributeJson = fileInput.getAttribute(attributeName)

    if (acceptAllowedExtensionsAttributeJson === null) {
        console.error(`Erreur de configuration: l'attribut '${attributeName}' est manquant`)
        fileInput.setCustomValidity("Erreur de configuration: extensions autorisées non définies")
        fileInput.reportValidity()
        return null
    }

    let allowedExtensions
    try {
        allowedExtensions = JSON.parse(acceptAllowedExtensionsAttributeJson)
    } catch (error) {
        console.error(`Erreur de configuration: l'attribut '${attributeName}' contient un JSON invalide`, error)
        fileInput.setCustomValidity("Erreur de configuration: format des extensions autorisées invalide")
        fileInput.reportValidity()
        return null
    }

    const currentDocumentType = documentTypeSelect.value
    const documentTypeAllowedExtensions = allowedExtensions[currentDocumentType]
    if (!documentTypeAllowedExtensions) {
        console.error(
            `Erreur de configuration: aucune extension définie dans l'attribut '${attributeName}' pour le type '${currentDocumentType}' ou pas de valeur par défaut`,
        )
        fileInput.setCustomValidity(`Erreur de configuration: aucune extension définie pour ce type de document`)
        fileInput.reportValidity()
        fileInput.setAttribute("accept", "")
        return null
    }

    return documentTypeAllowedExtensions
}

export function isSelectedFileExtensionValid(fileInput, documentTypeAllowedExtensions) {
    fileInput.setCustomValidity("")

    if (!fileInput.files || fileInput.files.length === 0) {
        return true
    }

    // Extraire l'extension du fichier
    const fileName = fileInput.files[0].name
    const fileExtension =
        fileName.lastIndexOf(".") !== -1 ? fileName.slice(fileName.lastIndexOf(".") + 1).toLowerCase() : ""
    if (!fileExtension) {
        fileInput.setCustomValidity("Le fichier sélectionné n'a pas d'extension")
        fileInput.reportValidity()
        return false
    }

    // Normaliser les extensions autorisées
    const formattedExtensions = documentTypeAllowedExtensions.split(",").map((ext) => ext.replace(/^\./, ""))

    // Vérifier si l'extension est autorisée
    if (!formattedExtensions.includes(fileExtension)) {
        fileInput.setCustomValidity(
            `L'extension du fichier n'est pas autorisé pour le type de document sélectionné (extensions autorisées : ${formattedExtensions.join(", ")})`,
        )
        fileInput.reportValidity()
        return false
    }

    return true
}

export function updateAcceptAttributeFileInput(
    fileInput,
    documentTypeSelect,
    documentTypeAllowedExtensions,
    extensionsInfoSpan,
) {
    // MAJ de l'attribut accept et de l'affichage des extensions autorisées
    fileInput.setAttribute("accept", documentTypeAllowedExtensions)
    extensionsInfoSpan.textContent = documentTypeAllowedExtensions
        .split(",")
        .map((ext) => ext.replace(".", ""))
        .join(", ")
}

export function removeEmptyOptionIfExist(selectElement) {
    const emptyOption = Array.from(selectElement.options).find((option) => option.value === "")
    if (emptyOption) {
        emptyOption.remove()
    }
}
