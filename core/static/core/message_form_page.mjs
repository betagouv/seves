import {Controller} from "Stimulus";
import choicesDefaults from "choicesDefaults"
import {applicationReady} from "Application"

export class MessageFormController extends Controller {
    static targets = ["recipients", "recipients_copy"]

    configureChoicesForRecipients(){
        if(this.hasRecipientsTarget){
            this.recipientChoices = new Choices(this.recipientsTarget, {
                ...choicesDefaults,
                removeItemButton: true,
                searchResultLimit: 500,
            })
        }
    }
    configureChoicesForCopy(){
        if(this.hasRecipients_copyTarget){
            this.recipientCopyChoices = new Choices(this.recipients_copyTarget, {
                ...choicesDefaults,
                removeItemButton: true,
                searchResultLimit: 500,
            })
        }
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
