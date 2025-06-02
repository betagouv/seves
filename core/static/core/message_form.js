import {
    getAcceptAllowedExtensionsAttributeValue,
    updateAcceptAttributeFileInput,
    validateFileSize,
    isSelectedFileExtensionValid,
    removeEmptyOptionIfExist
} from "./document.js";

let currentID = 0

function cloneDocumentInput(input, currentID, destination){
    let newFileInput = input.cloneNode()
    newFileInput.setAttribute("id", `document_file_${currentID}`)
    newFileInput.setAttribute("name", `document_file_${currentID}`)
    destination.appendChild(newFileInput)
}

function cloneDocumentTypeInput(input, currentID, destination){
    let newTypeInput = input.cloneNode(true)
    newTypeInput.setAttribute("id", `document_type_${currentID}`)
    newTypeInput.setAttribute("name", `document_type_${currentID}`)
    newTypeInput.value = input.value;
    destination.appendChild(newTypeInput)
}

function addDocumentCard(currentID, fileInput){
    const toShow = `<div class="fr-p-1w fr-mb-2w document-to-add" id="document_card_${currentID}">`
    + `<span>${fileInput.files[0].name}</span><a href="#" id="document_remove_${currentID}" data-document-id="${currentID}">`
    + `<span class="fr-icon-close-circle-line" aria-hidden="true"></span></a></div>`

    document.getElementById("documents-to-upload").insertAdjacentHTML("beforeend", toShow);
    const deleteButton = document.getElementById(`document_remove_${currentID}`)
    deleteButton.addEventListener("click", (event)=>{
        const documentID= event.target.parentNode.dataset.documentId
        document.getElementById(`document_card_${documentID}`).remove()
        document.getElementById(`document_type_${documentID}`).remove()
        document.getElementById(`document_file_${documentID}`).remove()
    });
}

function onDocumentTypeChange(typeInput, fileInput, messageAddDocumentButton, extensionsInfoSpan) {
    const documentTypeAllowedExtensions = getAcceptAllowedExtensionsAttributeValue(fileInput, typeInput);
    if (documentTypeAllowedExtensions === null) {
        messageAddDocumentButton.setAttribute("disabled", "true");
        return;
    }
    removeEmptyOptionIfExist(typeInput);
    fileInput.removeAttribute("disabled");
    updateAcceptAttributeFileInput(fileInput, typeInput, documentTypeAllowedExtensions, extensionsInfoSpan);
    const hasValidFile = fileInput.files && fileInput.files.length > 0 && isSelectedFileExtensionValid(fileInput, documentTypeAllowedExtensions);
    if (hasValidFile) {
        messageAddDocumentButton.removeAttribute("disabled");
    }
    else {
        messageAddDocumentButton.setAttribute("disabled", "true");
    }
}

function onFileInputChange(fileInput, typeInput, messageAddDocumentButton) {
    const documentTypeAllowedExtensions = getAcceptAllowedExtensionsAttributeValue(fileInput, typeInput);
    if (typeInput.value !== "" && validateFileSize(fileInput) && documentTypeAllowedExtensions !== null && isSelectedFileExtensionValid(fileInput, documentTypeAllowedExtensions)) {
        messageAddDocumentButton.removeAttribute("disabled")
    }
}

function addStructuresToRecipients(event, choiceElements, dataAttribute){
    event.preventDefault()
    choiceElements.forEach(element =>{element.setChoiceByValue(event.target.getAttribute(dataAttribute).split(","))})
}

function addShortcut(classToWatch, elements, dataAttribute){
    const destinatairesShortcutElement = document.querySelectorAll(classToWatch)
    destinatairesShortcutElement.forEach(shortcut => {
        shortcut.addEventListener("click", event => addStructuresToRecipients(event, elements, dataAttribute))
    })
}

function isLimitedRecipientsASelect(){
    return document.getElementById("id_recipients_limited_recipients").type === "select-multiple"
}

function getMessageConfig(){
    const helpElement = document.getElementById("point-situation-help")
    const destinatairesElement = document.querySelector('label[for="id_recipients"]').parentNode
    const destinatairesStructureElement = document.querySelector('label[for="id_recipients_structures_only"]').parentNode
    const destinatairesInput = document.getElementById("id_recipients")
    const destinatairesStructureInput = document.getElementById("id_recipients_structures_only")
    const copieElement = document.querySelector('label[for="id_recipients_copy"]').parentNode
    const copieStructuresElement = document.querySelector('label[for="id_recipients_copy_structures_only"]').parentNode

    let limitedRecipientsElement = null
    let limitedRecipientsInput = null
    if (isLimitedRecipientsASelect()) {
        limitedRecipientsElement = document.getElementById("id_recipients_limited_recipients").parentNode.parentNode.parentNode
        limitedRecipientsInput =  document.getElementById("id_recipients_limited_recipients")
    } else {
        limitedRecipientsElement = document.getElementById("id_recipients_limited_recipients").parentNode
    }
    const allElements = [destinatairesElement, copieElement, destinatairesStructureElement, copieStructuresElement, limitedRecipientsElement, helpElement]
    const allRequiredInputs = [destinatairesInput, destinatairesStructureInput]
    const configuration = {
        "compte rendu sur demande d'intervention": {
            toShow: [limitedRecipientsElement],
            required: []
        },
        "message": {
            toShow: [destinatairesElement, copieElement],
            required : [destinatairesInput]
        },
        "demande d'intervention": {
            toShow: [destinatairesStructureElement, copieStructuresElement],
            required: [destinatairesStructureInput]
        },
        "point de situation": {
            toShow: [helpElement],
            required: []
        }
    }
    if (isLimitedRecipientsASelect()) {
        configuration["compte rendu sur demande d'intervention"].required = [limitedRecipientsInput]
    }
    return [configuration, allElements, allRequiredInputs]
}

function changeFormBasedOnMessageType(messageType){
    document.getElementById("id_message_type").value=messageType
    document.getElementById("message-type-title").innerText=messageType

    const [configuration, allElements, allRequiredInputs] = getMessageConfig()
    allElements.forEach(element =>{element.classList.add("fr-hidden")})
    allRequiredInputs.forEach(element =>{element.required = false})

    if (messageType in configuration){
        configuration[messageType].toShow.forEach(element => {element.classList.remove("fr-hidden")})
        configuration[messageType].required.forEach(element => {element.required= true})
    }
    if (messageType === "fin de suivi") {
        document.getElementById("id_title").value = "Fin de suivi"
    } else {
        document.getElementById("id_title").value = ""
    }
}

function validateLimitedRecipients() {
    return Array.from(
        document.querySelectorAll("input[name='recipients_limited_recipients']")
    ).some(checkbox => checkbox.checked);
}

function updateLimitedRecipientsValidation() {
    const messageType = document.getElementById("id_message_type").value;
    if (messageType !== "compte rendu sur demande d'intervention") {
        return;
    }
    const firstCheckbox = document.querySelector("input[name='recipients_limited_recipients']");
    const errorMessage = validateLimitedRecipients() ? "" : "Veuillez sélectionner au moins un destinataire";
    firstCheckbox.setCustomValidity(errorMessage);
}

function initializeChoices(element){
    return new Choices(element, {
        removeItemButton: true,
        classNames: {containerInner: 'fr-select'},
        itemSelectText: '',
        searchResultLimit: 500,
    })
}

function addEmptyOptionInDocumentTypeSelect(typeInput) {
    const emptyOption = document.createElement("option");
    emptyOption.value = "";
    emptyOption.text = "Sélectionnez un type";
    typeInput.insertBefore(emptyOption, typeInput.firstChild);
}

function resetAddDocumentForm(typeInput, fileInput) {
    addEmptyOptionInDocumentTypeSelect(typeInput);
    typeInput.selectedIndex = 0;
    fileInput.value = null;
    fileInput.setAttribute("disabled", "true");
    document.getElementById("message-add-document").setAttribute("disabled", "true");
    currentID += 1;
    document.querySelector(".add-document-form-btn").classList.remove("fr-hidden");
    document.querySelector(".document-form").classList.add("fr-hidden");
}

function validateDocument(event, typeInput, fileInput, inputDestination){
    event.preventDefault();
    cloneDocumentInput(fileInput, currentID, inputDestination)
    cloneDocumentTypeInput(typeInput, currentID, inputDestination)
    addDocumentCard(currentID, fileInput)
    resetAddDocumentForm(typeInput, fileInput);
}

function onSubmitBtnClick(event, messageForm) {
    event.preventDefault()
    const messageStatusField = messageForm.querySelector("#id_status");

    messageStatusField.value = event.target.getAttribute("value");
    if (!isLimitedRecipientsASelect()) {
        updateLimitedRecipientsValidation();
    }
    messageForm.reportValidity()

    if (!messageForm.checkValidity()) {
        return
    }
    messageForm.querySelector("#draft-message-send-btn").disabled = true
    messageForm.querySelector("#message-send-btn").disabled = true

    const isDocumentBlockVisible = !document.querySelector(".document-form").classList.contains("fr-hidden")
    const hasFile = !!document.getElementById('id_file').files[0]

    if (isDocumentBlockVisible && hasFile) {
        dsfr(document.getElementById('fr-modal-document-confirmation')).modal.disclose();
    } else {
        messageForm.submit();
    }
}

function initUpdateMessageForm(messageUpdateForm){
    const recipientsElement = messageUpdateForm.querySelector('[id="id_recipients"]');
    const copyElement = messageUpdateForm.querySelector('[id="id_recipients_copy"]');
    const structuresRecipientsElement = messageUpdateForm.querySelector('[id="id_recipients_structures_only"]');
    const structuresCopyElement = messageUpdateForm.querySelector('[id="id_recipients_copy_structures_only"]');
    const limitRecipientsElement = messageUpdateForm.querySelector('[id="id_recipients_limited_recipients"]');

    const choicesRecipients = recipientsElement ? initializeChoices(recipientsElement) : null;
    const choicesCopy = copyElement ? initializeChoices(copyElement) : null;
    const choicesStructuresRecipients = structuresRecipientsElement ? initializeChoices(structuresRecipientsElement) : null;
    const choicesStructuresCopy = structuresCopyElement ? initializeChoices(structuresCopyElement) : null;
    if (isLimitedRecipientsASelect() && !!limitRecipientsElement) {
        initializeChoices(limitRecipientsElement)
    }

    const addListener = (selector, choices, dataType) => {
        messageUpdateForm
            .querySelector(selector)
        ?.addEventListener("click", event =>
            addStructuresToRecipients(event, [choices], dataType)
        );
    };

    if (choicesRecipients) {
        addListener(".destinataires-contacts-shortcut", choicesRecipients, "data-contacts");
        addListener(".destinataires-shortcut", choicesRecipients, "data-structures");
    }
    if (choicesCopy) {
        addListener(".copie-contacts-shortcut", choicesCopy, "data-contacts");
        addListener(".copie-shortcut", choicesCopy, "data-structures");
    }
    if (choicesStructuresRecipients) {
        addListener(".destinataires-shortcut", choicesStructuresRecipients, "data-structures");
    }
    if (choicesStructuresCopy) {
        addListener(".copie-shortcut", choicesStructuresCopy, "data-structures");
    }


    messageUpdateForm
        .querySelector("#draft-message-send-btn")
        .addEventListener("click", event =>
            onSubmitBtnClick(event, messageUpdateForm)
        );
    messageUpdateForm
        .querySelector("#message-send-btn")
        .addEventListener("click", event =>
            onSubmitBtnClick(event, messageUpdateForm)
        );
}

document.addEventListener('DOMContentLoaded', function () {
    const addMessageForm = document.getElementById("message-form");
    const addDocumentFormButton = document.querySelector(".add-document-form-btn")
    const messageAddDocumentButton = document.getElementById("message-add-document")
    const fileInput = document.getElementById('id_file');
    const typeInput = document.getElementById('id_document_type');
    const inputDestination = document.getElementById("inputs-for-upload")
    const extensionsInfoSpan = document.getElementById("allowed-extensions-list");
    const submitButton = document.getElementById("message-send-btn");
    const draftSubmitButton = document.getElementById("draft-message-send-btn");

    typeInput.addEventListener("change", () => onDocumentTypeChange(typeInput, fileInput, messageAddDocumentButton, extensionsInfoSpan));
    fileInput.addEventListener("change", () => onFileInputChange(fileInput, typeInput, messageAddDocumentButton));

    addDocumentFormButton.addEventListener("click", event =>{
        event.preventDefault();
        document.querySelector(".document-form").classList.remove("fr-hidden")
        addDocumentFormButton.classList.add("fr-hidden")
    })

    messageAddDocumentButton.addEventListener("click", event => {validateDocument(event, typeInput, fileInput,inputDestination)})
    const choicesRecipients = initializeChoices(document.getElementById('id_recipients'))
    const choicesCopy = initializeChoices(document.getElementById('id_recipients_copy'))
    const choicesStructuresRecipients = initializeChoices(document.getElementById('id_recipients_structures_only'))
    const choicesStructuresCopy = initializeChoices(document.getElementById('id_recipients_copy_structures_only'))
    if (isLimitedRecipientsASelect()) {
        initializeChoices(document.getElementById("id_recipients_limited_recipients"))
    }

    addShortcut(".destinataires-shortcut", [choicesRecipients, choicesStructuresRecipients], "data-structures");
    addShortcut(".copie-shortcut", [choicesCopy, choicesStructuresCopy], "data-structures");
    addShortcut(".destinataires-contacts-shortcut", [choicesRecipients], "data-contacts");
    addShortcut(".copie-contacts-shortcut", [choicesCopy], "data-contacts");
    document.querySelectorAll(".open-sidebar").forEach(element =>{
        element.addEventListener("click", event =>{
            changeFormBasedOnMessageType(event.target.dataset.messageType)
            if (!!event.target.dataset.recipient){
                choicesRecipients.setChoiceByValue(event.target.dataset.recipient)
            }
        })
    })

    submitButton.addEventListener("click", event => onSubmitBtnClick(event, addMessageForm));
    draftSubmitButton.addEventListener("click", event => onSubmitBtnClick(event, addMessageForm));
    document.getElementById("send-without-adding-document").addEventListener("click", event => {
        addMessageForm.submit()
    })
    document.getElementById("send-with-adding-document").addEventListener("click", event => {
        document.getElementById("message-add-document").click()
        addMessageForm.submit()
    })
    document.getElementById("fr-modal-document-confirmation").addEventListener("dsfr.disclose", event => {
        submitButton.disabled = false;
        draftSubmitButton.disabled = false;
    });

    document.querySelectorAll('[id^="sidebar-message-"]').forEach(messageContainer => {
        const messageUpdateForm = messageContainer.querySelector("form");
        if (!messageUpdateForm) {
            return;
        }
        initUpdateMessageForm(messageUpdateForm)

    });

});
