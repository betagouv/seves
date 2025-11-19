import {Controller} from "Stimulus";
import choicesDefaults from "choicesDefaults"
import {applicationReady} from "Application"
import {collectFormValues} from "Forms"
import {validateFileSize, updateAcceptAttributeFileInput, getAcceptAllowedExtensionsAttributeValue, isSelectedFileExtensionValid} from "Document"

export class MessageFormController extends Controller {
    static targets = ["recipients", "recipients_copy", "draftBtn", "sendBtn", "documentTypeSelect", "documentNameInput", "addDocument", "documentFile", "commentInput","cardsContainer","allowedExtensions", "inputsContainer"]
    documents = []

    configureChoicesForRecipients(){
        if(this.hasRecipientsTarget && this.recipientsTarget instanceof HTMLSelectElement){
            this.recipientChoices = new Choices(this.recipientsTarget, {
                ...choicesDefaults,
                removeItemButton: true,
                searchResultLimit: 500,
                callbackOnInit: function() {
                    this.passedElement.element.addEventListener('change', () => {
                        this.hideDropdown(true);
                    });
                }
            })
        }
    }
    configureChoicesForCopy(){
        if(this.hasRecipients_copyTarget){
            this.recipientCopyChoices = new Choices(this.recipients_copyTarget, {
                ...choicesDefaults,
                removeItemButton: true,
                searchResultLimit: 500,
                callbackOnInit: function() {
                    this.passedElement.element.addEventListener('change', () => {
                        this.hideDropdown(true);
                    });
                }
            })
        }
    }

    addHiddenInput(name, value)  {
        const input = document.createElement("input")
        input.type = "hidden"
        input.name = name
        input.value = value
        this.element.appendChild(input)
    }

    addDocumentsInput(){
        this.documents.forEach((doc, i) => {
            this.addHiddenInput(`document_type_${i}`, doc.type)
            this.addHiddenInput(`document_name_${i}`, doc.name)
            this.addHiddenInput(`document_comment_${i}`, doc.comment)
            const fileInput = document.createElement("input")
            fileInput.type = "file"
            fileInput.name = `document_file_${i}`
            const dt = new DataTransfer()
            dt.items.add(doc.file)
            fileInput.files = dt.files
            fileInput.classList.add("fr-hidden")
            this.element.appendChild(fileInput)
        })
    }

    onSend(event){
        if (event.isTrusted === false) {
            // Make the form verification only for a human click: allows us to send the form for real when we need to
            return
        }

        event.preventDefault()
        this.documentNameInputTarget.required = false
        this.documentTypeSelectTarget.required = false
        this.documentFileTarget.required = false

        const formValues = collectFormValues(this.element)
        if (formValues === undefined) {
            this.documentNameInputTarget.required = true
            this.documentTypeSelectTarget.required = true
            this.documentFileTarget.required = true
            return
        }

        this.addDocumentsInput()
        event.target.click()
        this.draftBtnTarget.disabled = true
        this.sendBtnTarget.disabled = true
    }

    onShortcutDestinataires(event){
        this.recipientChoices.setChoiceByValue(event.target.dataset.contacts.split(","))
    }

    onShortcutCopie(event){
        this.recipientCopyChoices.setChoiceByValue(event.target.dataset.contacts.split(","))
    }

    _setSendButtonState(){
        this.addDocumentTarget.disabled = !(this.documentNameInputTarget.value && this.documentTypeSelectTarget.value && this.documentFileTarget.value)
    }

    _setAddFileButtonState(){
        this.documentFileTarget.disabled = !(this.documentNameInputTarget.value && this.documentTypeSelectTarget.value)
    }

    onNomChanged(){
        this._setSendButtonState()
        this._setAddFileButtonState()
    }

    onTypeChanged(){
        this._setAddFileButtonState()
        this._setSendButtonState()
        const documentTypeAllowedExtensions = getAcceptAllowedExtensionsAttributeValue(this.documentFileTarget, this.documentTypeSelectTarget);
        updateAcceptAttributeFileInput(this.documentFileTarget, this.documentTypeSelectTarget, documentTypeAllowedExtensions, this.allowedExtensionsTarget)
    }

    onFileChanged(){
        this._setSendButtonState()
        validateFileSize(this.documentFileTarget)
        const documentTypeAllowedExtensions = getAcceptAllowedExtensionsAttributeValue(this.documentFileTarget, this.documentTypeSelectTarget);
        isSelectedFileExtensionValid(this.documentFileTarget, documentTypeAllowedExtensions)
    }

    onDeleteDocument(event){
        event.target.parentNode.parentNode.remove()
        this.documents = this.documents.filter(function(item) {return item.id != event.target.parentNode.dataset.documentId})
        if (this.documents.length === 0){
            this.cardsContainerTarget.innerText = "Aucun documents ajouté"
        }
    }

    addDocumentCard(filename){
        const card = `<div class="fr-p-1w fr-mb-2w document-to-add" id="document_card_${this.currentDocumentID}">
                        <span>${filename}</span>
                        <a href="#" data-action="click->message-form#onDeleteDocument" data-document-id="${this.currentDocumentID}">
                            <span class="fr-icon-close-circle-line" aria-hidden="true"></span>
                        </a>
                    </div>`

        if (this.documents.length === 0){
            this.cardsContainerTarget.innerHTML = ""
        }
        this.cardsContainerTarget.insertAdjacentHTML("beforeend", card);
    }

    onAddDocument(){
        const doc = {
            id: this.currentDocumentID,
            type: this.documentTypeSelectTarget.value,
            file: this.documentFileTarget.files[0],
            name: this.documentNameInputTarget.value,
            comment: this.commentInputTarget.value,
        }
        this.addDocumentCard(this.documentNameInputTarget.value)
        this.documents.push(doc)

        this.documentTypeSelectTarget.selectedIndex = 0
        this.documentFileTarget.value = null
        this.documentNameInputTarget.value = ""
        this.commentInputTarget.value = ""
        this.currentDocumentID += 1;
        this.documentFileTarget.disabled = true
        this.addDocumentTarget.disabled = true
    }

    connect() {
        this.configureChoicesForRecipients()
        this.configureChoicesForCopy()
        this.currentDocumentID = 0
    }

}

applicationReady.then(app => {
    app.register("message-form", MessageFormController)
})
