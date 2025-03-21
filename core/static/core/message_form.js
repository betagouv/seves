import { validateFileSize } from "./document.js";
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

function allowToUploadWhenTypeIsSelected(typeInput, fileInput,messageAddDocumentButton){
    typeInput.addEventListener("change", ()=>{
        if (typeInput.value !== ""){
            fileInput.removeAttribute("disabled")
        } else {
            messageAddDocumentButton.setAttribute("disabled", "true")
        }
    })
}

function allowToValidateWhenDocumentIsSelectedAndValidSize(typeInput, fileInput,messageAddDocumentButton){
    fileInput.addEventListener("change", ()=>{
        if (typeInput.value !== "" && validateFileSize(fileInput)){
            messageAddDocumentButton.removeAttribute("disabled")
        }
    })
}

function addStructuresToRecipients(event, choiceElements){
    event.preventDefault()
    choiceElements.forEach(element =>{element.setChoiceByValue(event.target.getAttribute("data-structures").split(","))})
}

function addShortcut(classToWatch, elements){
    const destinatairesShortcutElement = document.querySelectorAll(classToWatch)
    destinatairesShortcutElement.forEach(shortcut => {
        shortcut.addEventListener("click", event => addStructuresToRecipients(event, elements))
    })
}

function getMessageConfig(){
    const helpElement = document.getElementById("point-situation-help")
    const destinatairesElement = document.querySelector('label[for="id_recipients"]').parentNode
    const destinatairesStructureElement = document.querySelector('label[for="id_recipients_structures_only"]').parentNode
    const destinatairesInput = document.getElementById("id_recipients")
    const destinatairesStructureInput = document.getElementById("id_recipients_structures_only")
    const copieElement = document.querySelector('label[for="id_recipients_copy"]').parentNode
    const copieStructuresElement = document.querySelector('label[for="id_recipients_copy_structures_only"]').parentNode
    const limitedRecipientsElement = document.getElementById("id_recipients_limited_recipients").parentNode
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

function validateDocument(event, typeInput, fileInput, inputDestination){
    event.preventDefault();

    cloneDocumentInput(fileInput, currentID, inputDestination)
    cloneDocumentTypeInput(typeInput, currentID, inputDestination)
    addDocumentCard(currentID, fileInput)

    // Reset form
    typeInput.selectedIndex = 0
    fileInput.value = null
    fileInput.setAttribute("disabled", "true")
    document.getElementById("message-add-document").setAttribute("disabled", "true")
    currentID += 1;
    document.querySelector(".add-document-form-btn").classList.remove("fr-hidden")
    document.querySelector(".document-form").classList.add("fr-hidden")
}

document.addEventListener('DOMContentLoaded', function () {
    const addDocumentFormButton = document.querySelector(".add-document-form-btn")
    const messageAddDocumentButton = document.getElementById("message-add-document")
    const fileInput = document.getElementById('id_file');
    const typeInput = document.getElementById('id_document_type');
    const inputDestination = document.getElementById("inputs-for-upload")

    allowToUploadWhenTypeIsSelected(typeInput, fileInput, messageAddDocumentButton)
    allowToValidateWhenDocumentIsSelectedAndValidSize(typeInput, fileInput, messageAddDocumentButton)

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


    addShortcut(".destinataires-shortcut", [choicesRecipients, choicesStructuresRecipients]);
    addShortcut(".copie-shortcut", [choicesCopy, choicesStructuresCopy]);
    document.querySelectorAll(".message-panel").forEach(element =>{
        element.addEventListener("click", event =>{
            changeFormBasedOnMessageType(event.target.dataset.messageType)
            if (!!event.target.dataset.recipient){
                choicesRecipients.setChoiceByValue(event.target.dataset.recipient)
            }
        })
    })

    document.getElementById("message-send-btn").addEventListener("click", event =>{
        event.preventDefault()
        const messageForm = document.getElementById("message-form")

        updateLimitedRecipientsValidation();
        messageForm.reportValidity()

        if (!messageForm.checkValidity()) {
            return
        }
        event.target.disabled = true

        const isDocumentBlockVisible = !document.querySelector(".document-form").classList.contains("fr-hidden")
        const hasFile = !!document.getElementById('id_file').files[0]

        if (isDocumentBlockVisible && hasFile) {
            dsfr(document.getElementById('fr-modal-document-confirmation')).modal.disclose();
        } else {
            event.target.closest("form").submit()
        }
    })

    document.getElementById("send-without-adding-document").addEventListener("click", event => {
        document.getElementById("message-form").submit()
    })
    document.getElementById("send-with-adding-document").addEventListener("click", event => {
        document.getElementById("message-add-document").click()
        document.getElementById("message-form").submit()
    })

});
