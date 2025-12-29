import choicesDefaults from "choicesDefaults"
import {applicationReady} from "Application";
import {Controller} from "Stimulus";
import {getSelectedLabel} from "Forms"

class PermissionsAdminsFormController  extends Controller {
    static targets = [
        "selectUser",
        "submitBtn",
        "confirmModal",
        "modalContent",
        "form"
    ]

    connect() {
        const options = {
            ...choicesDefaults,
            removeItemButton: false,
            placeholderValue: "Choisir dans la liste",
            searchPlaceholderValue: "Choisir dans la liste",
        };
        this.choices = new Choices(this.selectUserTarget, options);
        this.choices.passedElement.element.addEventListener("choice", ()=> {this.handleButtonState()})
    }

    handleButtonState(){
        this.submitBtnTarget.disabled = !(!!this.choices.getValue(true) && this.element.qu)
        const hasChoice = this.choices.getValue(true)?.length > 0
        const hasChecked = this.element.querySelectorAll('input[type="checkbox"]:checked').length > 0
        this.submitBtnTarget.disabled = !(hasChoice && hasChecked)
    }

    onSubmitForm(){
        this.modalContentTarget.innerText= "Vous êtes sur le point de donner à " + getSelectedLabel(this.selectUserTarget) + " la possibilité de donner les droits d’accès à Sèves pour sa structure, êtes-vous sûr de vouloir poursuivre ? "
        dsfr(this.confirmModalTarget).modal.disclose();
    }

    onConfirm(){
        this.formTarget.submit()
    }

}

applicationReady.then(app => {
    app.register("permissions-admin-form", PermissionsAdminsFormController)
})
