import {Controller} from "Stimulus";
import choicesDefaults from "choicesDefaults"
import {applicationReady} from "Application"
import {collectFormValues} from "Forms"
import {
    validateFileSize,
    updateAcceptAttributeFileInput,
    getAcceptAllowedExtensionsAttributeValue,
    isSelectedFileExtensionValid
} from "Document"

/**
 * @property {HTMLFormElement} element
 * @property {HTMLButtonElement} draftBtnTarget
 * @property {HTMLButtonElement} sendBtnTarget
 */
export class MessageFormController extends Controller {
    static targets = [
        "recipients",
        "recipients_copy",
        "draftBtn",
        "sendBtn",
        "allowedExtensions",
    ]
    documents = []

    configureChoicesForRecipients() {
        if(this.hasRecipientsTarget && this.recipientsTarget instanceof HTMLSelectElement) {
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

    configureChoicesForCopy() {
        if(this.hasRecipients_copyTarget) {
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

    /** @param {MouseEvent} event */
    onSend(event) {
        if(event.isTrusted === false) {
            // Make the form verification only for a human click: allows us to send the form for real when we need to
            return
        }

        event.preventDefault()
        event.target.click()
        if(this.element.reportValidity()) {
            this.draftBtnTarget.disabled = true
            this.sendBtnTarget.disabled = true
        }
    }

    onShortcutDestinataires(event) {
        this.recipientChoices.setChoiceByValue(event.target.dataset.contacts.split(","))
    }

    onShortcutCopie(event) {
        this.recipientCopyChoices.setChoiceByValue(event.target.dataset.contacts.split(","))
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
