
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

function allowToValidateWhenDocumentIsSelected(typeInput, fileInput,messageAddDocumentButton){
    fileInput.addEventListener("change", ()=>{
        if (typeInput.value !== ""){
            messageAddDocumentButton.removeAttribute("disabled")
        }
    })
}

function addStructuresToRecipients(event, choiceElement){
    event.preventDefault()
    choiceElement.setChoiceByValue(event.target.getAttribute("data-structures").split(","))
}

function addShortcuts(choicesRecipients, choicesCopy){
    const destinatairesShortcutElement = document.querySelector(".destinataires-shortcut")
    if (!! destinatairesShortcutElement){
        destinatairesShortcutElement.addEventListener("click", event => addStructuresToRecipients(event, choicesRecipients))
    }
    const copieShortcutElement = document.querySelector(".copie-shortcut")
    if (!! destinatairesShortcutElement){
        copieShortcutElement.addEventListener("click", event => addStructuresToRecipients(event, choicesCopy))
    }
}

document.addEventListener('DOMContentLoaded', function () {
    let currentID = 0
    const messageAddDocumentButton = document.getElementById("message-add-document")
    const fileInput = document.getElementById('id_file');
    const typeInput = document.getElementById('id_document_type');
    const inputDestination = document.getElementById("inputs-for-upload")
    const noDocumentBlock = document.getElementById("no-document")

    allowToUploadWhenTypeIsSelected(typeInput, fileInput, messageAddDocumentButton)
    allowToValidateWhenDocumentIsSelected(typeInput, fileInput, messageAddDocumentButton)

    messageAddDocumentButton.addEventListener("click", function (event) {
        event.preventDefault();

        noDocumentBlock.classList.add("fr-hidden")

        cloneDocumentInput(fileInput, currentID, inputDestination)
        cloneDocumentTypeInput(typeInput, currentID, inputDestination)
        addDocumentCard(currentID, fileInput)

        // Reset form
        typeInput.selectedIndex = 0
        fileInput.value = null
        fileInput.setAttribute("disabled", "true")
        messageAddDocumentButton.setAttribute("disabled", "true")
        currentID += 1;

    });

    const choicesRecipients = new Choices(document.getElementById('id_recipients'), {
        removeItemButton: true,
        classNames: {containerInner: 'fr-select'},
        itemSelectText: '',
        searchResultLimit: 500,
    });
    const choicesCopy = new Choices(document.getElementById('id_recipients_copy'), {
        removeItemButton: true,
        classNames: {containerInner: 'fr-select'},
        itemSelectText: '',
        searchResultLimit: 500,
    });

    addShortcuts(choicesRecipients, choicesCopy);
    document.querySelectorAll(".message-panel").forEach(element =>{
        element.addEventListener("click", event =>{
            document.getElementById('sidebar').classList.toggle('open');
            document.querySelector('.main-container').classList.toggle('open')
            document.getElementById("id_message_type").value=event.target.dataset.messageType

            const messageType = event.target.dataset.messageType
            const destinatairesElement = document.querySelector('label[for="id_recipients"]').parentNode
            const destinatairesInput = document.getElementById("id_recipients")
            const copieElement = document.querySelector('label[for="id_recipients_copy"]').parentNode

            if (messageType === "note" || messageType === "point de situation" || messageType === "fin de suivi") {
                destinatairesElement.classList.add("fr-hidden")
                destinatairesInput.required = false
                copieElement.classList.add("fr-hidden")
            } else if (messageType === "compte rendu sur demande d'intervention") {
                destinatairesElement.classList.add("fr-hidden")
                destinatairesInput.required = false
                copieElement.classList.add("fr-hidden")
                document.getElementById("id_recipients_limited_recipients").parentNode.classList.remove("fr-hidden")
            } else {
                destinatairesElement.classList.remove("fr-hidden")
                destinatairesInput.required = true
                copieElement.classList.remove("fr-hidden")
            }
            if (messageType === "fin de suivi") {
                document.getElementById("id_title").value = "Fin de suivi"
            } else {
                document.getElementById("id_title").value = ""
            }

        })
    })

    document.querySelectorAll(".close-sidebar").forEach(element => {element.addEventListener("click", event =>{
        document.getElementById('sidebar').classList.toggle('open');
        document.querySelector('.main-container').classList.toggle('open')
    })})
});
