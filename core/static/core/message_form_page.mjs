import {Controller} from "Stimulus";
import choicesDefaults from "choicesDefaults"
import {applicationReady} from "Application"
import {collectFormValues} from "Forms"

export class MessageFormController extends Controller {
    static targets = ["recipients", "recipients_copy", "draftBtn", "sendBtn"]

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

    onSend(event){
        if (event.isTrusted === false){
            return
        }

        event.preventDefault()
        const formValues = collectFormValues(this.element)
        if (formValues === undefined) {
            return
        }
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

    connect() {
        this.configureChoicesForRecipients()
        this.configureChoicesForCopy()
    }

}

applicationReady.then(app => {
    app.register("message-form", MessageFormController)
})
