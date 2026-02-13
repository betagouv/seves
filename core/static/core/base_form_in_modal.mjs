import { Controller } from "Stimulus"
import { collectFormValues, removeRequired } from "Forms"

/**
 * Base controller for forms that generate cards and handle deletion.
 * @property {HTMLElement[]} cardContainerTargets
 * @property {HTMLFormElement} fieldsetTarget
 * @property {HTMLInputElement} deleteInputTarget
 * @property {HTMLDialogElement} dialogTarget
 * @property {HTMLDialogElement} deleteModalTarget
 * @property {String} formPrefixValue
 */
export class BaseFormInModal extends Controller {
    static targets = ["fieldset", "deleteInput", "dialog", "cardContainer", "deleteModal"]
    static values = { formPrefix: String, shouldImmediatelyShow: { type: Boolean, default: false } }

    openDialog() {
        dsfr(this.dialogTarget).modal.disclose()
    }

    closeDialog() {
        dsfr(this.dialogTarget).modal.conceal()
    }

    onValidateForm() {
        const formValues = collectFormValues(this.fieldsetTarget, {
            nameTransform: (name) => name.replace(`${this.formPrefixValue}-`, ""),
        })
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
        this.forceDelete()
        dsfr(this.deleteModalTarget).modal.conceal()
    }

    onCancelDelete() {
        dsfr(this.deleteModalTarget).modal.conceal()
    }

    forceDelete() {
        this.deleteInputTarget.value = "on"
        removeRequired(this.fieldsetTarget)
        this.element.classList.add("fr-hidden")
    }

    /**
     * Initializes the card with form data.
     * @abstract
     * @param {Object} data - The data to display.
     */
    initCard(data) {
        throw new Error("initCard must be implemented in the child class.")
    }

    /**
     * Renders the HTML for the card.
     * @abstract
     * @param {Object} data - The data to render.
     * @returns {string} HTML
     */
    renderCard(data) {
        throw new Error("renderCard must be implemented in the child class.")
    }

    /**
     * @abstract
     * @param {Object} data
     * @return {string}
     */
    getDeleteConfirmationSentence(data) {
        throw new Error("getDeleteConfirmationSentence must be implemented in the child class.")
    }

    /**
     * @abstract
     * @param {Object} data
     * @return {string}
     */
    getDeleteConfirmationTitle(data) {
        throw new Error("getDeleteConfirmationTitle must be implemented in the child class.")
    }

    optionalText(value, text) {
        return value ? text || `${value}` : ""
    }

    joinText(delimiter, ...items) {
        return items.filter((it) => !!it.length).join(delimiter)
    }

    renderBadges(items) {
        return items
            .filter((it) => !!it?.length)
            .map((it) => `<p class="fr-badge fr-badge--sm fr-badge--info fr-badge--no-icon fr-m-0 fr-mt-2v">${it}</p>`)
            .join("")
    }

    formatDate(value) {
        const [date, time] = value.split("T")
        const [year, month, day] = date.split("-")
        return `${day}/${month}/${year} ${time}`
    }

    /**
     * Renders the HTML for the delete confirmation modal.
     * @param {Object} data - The data for the modal.
     * @returns {string} HTML
     */
    renderDeleteConfirmationDialog(data) {
        // This can be a generic template or a method to be overridden.
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
                                <div class="fr-modal__header">
                                    <button
                                        class="fr-btn--close fr-btn"
                                        title="Fermer"
                                        aria-controls="${this.formPrefixValue}-delete-modal"
                                        type="button"
                                    >Fermer</button>
                                </div>
                                <div class="fr-modal__content">
                                    <h3 id="delete-modal-title" class="fr-modal__title">
                                        <span class="fr-icon-arrow-right-line fr-icon--lg" aria-hidden="true"></span>
                                        ${this.getDeleteConfirmationTitle(data)}
                                    </h3>
                                    <p>${this.getDeleteConfirmationSentence(data)}</p>
                                </div>
                                <div class="fr-modal__footer">
                                    <div class="fr-btns-group fr-btns-group--right fr-btns-group--inline-lg">
                                        <button
                                            class="fr-btn fr-btn--secondary delete-cancel"
                                            data-action="${this.identifier}#onCancelDelete:prevent:default"
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
