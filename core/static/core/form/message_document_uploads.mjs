import {applicationReady, COMMON_EVENTS, fetchPool} from "Application"
import {BaseDocumentFormset, DOCUMENT_FORM_ID, DOCUMENT_FORMSET_ID, DocumentForm} from "DocumentUploads"
import {Controller} from "Stimulus"

const STATES = Object.freeze({
    IDLE: 0,
    LOADING: 1,
    ERROR: 0,
})

/**
 * @property {HTMLElement} documentsAddedMsgTarget
 * @property {HTMLElement} validatedSectionTarget
 * @property {HTMLTemplateElement} validatedTplTarget
 * @property {HTMLElement[]} documentCardTargets
 * @property {Number} stateValue
 * @property {String[]} loadingClasses
 * @property {MessageDocumentCard[]} cardOutlets
 */
class MessageDocuments extends Controller {
    static targets = ["documentsAddedMsg", "validatedSection", "validatedTpl", "documentCard"]

    initialize() {
        const dataAction = [
            this.element.dataset.action || "",
            `window:${COMMON_EVENTS.DOCUMENT_SUCCESS}@window->${this.identifier}#onDocumentSuccess`,
        ]
        this.element.dataset.action = dataAction.join(" ").trim()
    }

    connect() {
        this.#updateMessage()
    }

    /** @param {String} documentNamesJSON */
    onDocumentSuccess({detail}) {
        for (const [pk, documentName] of Object.entries(detail[COMMON_EVENTS.DOCUMENT_SUCCESS])) {
            const existingCard = this.element.querySelector(`#document-form-${pk}`)

            const html = this.validatedTplTarget.innerHTML
                .replaceAll("__document_title__", documentName)
                .replaceAll("__pk__", pk)

            if (existingCard !== null) {
                existingCard.innerHTML = html
            } else {
                this.validatedSectionTarget.insertAdjacentHTML("beforeend", html)
            }
        }
    }

    documentCardTargetConnected() {
        this.#updateMessage()
    }

    documentCardTargetDisconnected() {
        this.#updateMessage()
    }

    #updateMessage() {
        this.documentsAddedMsgTarget.innerText =
            this.documentCardTargets.length === 0 ? "Aucun document ajouté" : "Documents ajoutés au message"
    }
}

/**
 * @property {HTMLElement} element
 * @property {HTMLInputElement} inputIdTarget
 * @property {HTMLElement} deleteBtnTarget
 * @property {Number} stateValue
 * @property {String[]} loadingClasses
 */
class MessageDocumentCard extends Controller {
    static targets = ["deleteBtn", "inputId"]
    static values = {state: {type: Number, default: STATES.IDLE}}
    static classes = ["loading"]

    initialize() {
        const dataAction = [
            this.element.dataset.action || "",
            `window:${COMMON_EVENTS.DOCUMENT_DELETE}@window->${this.identifier}#onDocumentRemoved`,
        ]
        this.element.dataset.action = dataAction.join(" ").trim()
    }

    stateValueChanged(state) {
        this.element.classList.remove(...this.loadingClasses)
        this.deleteBtnTarget.disabled = false

        if (state === STATES.LOADING) {
            this.element.classList.add(...this.loadingClasses)
            this.deleteBtnTarget.disabled = true
        }
    }

    onDocumentRemoved({detail}) {
        if (detail[COMMON_EVENTS.DOCUMENT_DELETE] === this.inputIdTarget.value) {
            this.element.remove()
        }
    }

    /**
     * @param {HTMLFormElement} target
     * @return {Promise<void>}
     */
    async onDelete({target}) {
        this.stateValue = STATES.LOADING
        try {
            const result = await fetchPool(target.action, {
                body: new FormData(target),
                method: target.method,
                redirect: "error",
            })
            if (result.ok) {
                this.element.remove()
                this.dispatch(COMMON_EVENTS.DOCUMENT_DELETE, {
                    detail: {[COMMON_EVENTS.DOCUMENT_DELETE]: this.inputIdTarget.value},
                    target: window,
                    prefix: "window",
                })
            }
        } catch (_) {
            this.stateValue = STATES.ERROR
        }
    }
}

class DocumentFormset extends BaseDocumentFormset {
    onModalClose() {
        super.onModalClose()
        this.documentFormOutlets.forEach(it => it.onModalClose())
    }
}

applicationReady.then(app => {
    app.register(DOCUMENT_FORM_ID, DocumentForm)
    app.register(DOCUMENT_FORMSET_ID, DocumentFormset)
    app.register("message-documents", MessageDocuments)
    app.register("message-document-card", MessageDocumentCard)
})
