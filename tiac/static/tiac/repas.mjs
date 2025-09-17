import {BaseFormSetController} from "BaseFormset"
import {applicationReady} from "Application";
import {Controller} from "Stimulus";
import {collectFormValues} from "Forms"

class RepasFormController extends Controller {
    static targets = [
        "dialog",
        "fieldset",
        "denominationInput",
        "deleteModal",
        "deleteInput",
        "cardContainer",
    ]
    static values = {formPrefix: String}

    connect() {
        this.openDialog()
    }

    openDialog() {
        dsfr(this.dialogTarget).modal.disclose()
    }

    closeDialog() {
        dsfr(this.dialogTarget).modal.conceal()
    }

    onValidateForm(){
        const formValues = collectFormValues(this.fieldsetTarget, name => name.replace(`${this.formPrefixValue}-`, ""))
        if (formValues === undefined) {
            return
        }

        this.initCard(formValues)
    }

    onModify() {
        this.openDialog()
    }

    onDelete() {
        dsfr(this.deleteModalTarget).modal.disclose()
    }

    onDeleteConfirm() {
        dsfr(this.deleteModalTarget).modal.conceal()
        this.deleteInputTarget.value = "on"
        this.element.classList.add("fr-hidden")
    }

    initCard(repas) {
        this.cardContainerTargets.forEach(it => it.remove())
        this.element.insertAdjacentHTML("beforeend", this.renderCard(repas))
        this.element.insertAdjacentHTML("beforeend", this.renderDeleteConfirmationDialog(repas))
        dsfr(this.dialogTarget).modal.conceal()
    }

    /**
     * @return {string} HTML
     */
    renderCard(repas) {
        function optional(value, text) {
            return value ? (text || `${value}`) : ""
        }
        function join(delimiter, ...items) {
            return items.filter(it => !!it.length).join(delimiter)
        }
        function formatDate(value){
            const [date, time] = value.split("T");
            const [year, month, day] = date.split("-");
            return`${day}/${month}/${year} ${time}`;
        }

        // languague=HTML
        return `<div class="repas-card fr-card" data-${this.identifier}-target="cardContainer">
            <div class="fr-card__body">
                <div class="fr-card__content">
                    <h3 class="fr-card__title" data-${this.identifier}-target="denomination">
                      ${repas.denomination}
                    </h3>
                    <div class="fr-card__desc">
                        ${optional(repas.datetime_repas, `<p>${formatDate(repas.datetime_repas)}</p>`)}
                        ${optional(repas.type_repas, `<p>${repas.type_repas}</p>`)}
                        ${optional(
                            repas.nombre_participant,
                            `<p class="fr-badge fr-badge--info">${repas.nombre_participant} participant(s)</p>`
                        )}
                    </div>
                </div>
                <div class="fr-card__footer">
                    <div class="fr-btns-group fr-btns-group--inline fr-btns-group--sm fr-btns-group--right">
                        <button
                            class="fr-btn fr-btn--secondary fr-icon-edit-line fr-mb-0 modify-button"
                            type="button"
                            data-action="${this.identifier}#onModify:prevent:default"
                        >Modifier</button>
                        <button
                            class="fr-btn fr-btn--secondary fr-icon-delete-bin-line fr-mb-0 delete-button"
                            type="button"
                            data-action="${this.identifier}#onDelete:prevent:default"
                        >Supprimer</button>
                    </div>
                </div>
            </div>
        </div>`
    }

    /**
     * @return {string} HTML
     */
    renderDeleteConfirmationDialog(repas) {
        // languague=HTML
        return `<button class="fr-btn fr-hidden" data-fr-opened="false" aria-controls="${this.formPrefixValue}-delete-modal"></button>
            <dialog
                id="${this.formPrefixValue}-delete-modal"
                class="fr-modal delete-modal"
                aria-labelledby="delete-modal-title"
                aria-modal="true"
                data-${this.identifier}-target="deleteModal"
            >
                <div class="fr-container fr-container--fluid">
                    <div class="fr-grid-row fr-grid-row--center">
                        <div class="fr-col-12 fr-col-md-8 fr-col-lg-6">
                            <div class="fr-modal__body">
                            <div class="fr-modal__header"></div>
                                <div class="fr-modal__content">
                                    <h3 id="delete-modal-title" class="fr-modal__title">
                                        <span class="fr-icon-arrow-right-line fr-icon--lg" aria-hidden="true"></span>
                                        Suppression d'un repas
                                    </h3>
                                    <p>Confimez-vous vouloir supprimer le repas ${repas.denomination}</p>
                                </div>
                                <div class="fr-modal__footer">
                                    <div class="fr-btns-group fr-btns-group--right fr-btns-group--inline-lg">
                                        <button
                                            class="fr-btn fr-btn--secondary delete-cancel"
                                            data-action="${this.identifier}#closeDialog:prevent:default"
                                        >Annuler</button>
                                        <button
                                            class="fr-btn delete-confirmation"
                                            data-action="${this.identifier}#onDeleteConfirm:prevent:default"
                                        >Supprimer</button>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </dialog>`
    }
}

applicationReady.then(app => {
    app.register("repas-formset", BaseFormSetController)
    app.register("repas-form", RepasFormController)
})
