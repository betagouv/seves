import { Controller } from "Stimulus"
import { COMMON_EVENTS, dsfrDisclosePromise, escapeHTML, fetchPool } from "Application"
import { createStore, useStore } from "StimulusStore"

const DOCUMENT_FORM_ID = "document-form"
const DOCUMENT_FORMSET_ID = "document-formset"

const DOCUMENT_STATE = Object.freeze({
    IDLE: 1,
    LOADING: 2,
    DELETING: 3,
    SUCCESS: 4,
    ERROR: 5,
})

const globalFileTypeIndexStore = createStore({
    name: "globalFileTypeIndex",
    type: Number,
    initialValue: 0,
})

const fileStore = createStore({
    name: "files",
    type: Object,
    initialValue: {},
})

const allowedExtensionsStore = createStore({
    name: "allowedExtensions",
    type: Object,
    initialValue: {},
})

class FormValidationError extends Error {
    constructor() {
        super("Invalid form")
        this.name = "FormValidationError"
    }
}

class ServerError extends Error {
    constructor() {
        super("Server error")
        this.name = "ServerError"
    }
}

/** @typedef {Object<String, File>} FileStoreStruct */

/**
 * @typedef {Object} StorePropertiesType
 *
 * @property {FileStoreStruct} filesValue
 * @property {import("StimulusStore/dist/types/updateMethod").UpdateMethod} setFilesValue
 * @property {function(FileStoreStruct): void} onFilesUpdate
 *
 * @property {Number} globalFileTypeIndexValue
 * @property {import("StimulusStore/dist/types/updateMethod").UpdateMethod} setGlobalFileTypeIndexValue
 * @property {function(Number): void} onGlobalFileTypeIndexUpdate
 *
 * @property {Number} allowedExtensionsValue
 * @property {import("StimulusStore/dist/types/updateMethod").UpdateMethod} setAllowedExtensionsValue
 * @property {function(Number): void} onAllowedExtensionsValueUpdate
 */

/**
 * @extends StorePropertiesType
 *
 * @property {Number} stateValue
 * @property {Boolean} uploadDisabledValue
 * @property {Object} allowedExtensionsValue
 * @property {String} nextUrlValue
 * @property {String} genericErrorValue
 *
 * @property {HTMLElement} errorContainerTarget
 * @property {HTMLTemplateElement} errorMessageTplTarget
 * @property {HTMLDialogElement} modalTarget
 * @property {HTMLTemplateElement} emptyFormTplTarget
 * @property {HTMLElement} formsetContainerTarget
 * @property {HTMLElement} allowedExtensionsTarget
 * @property {HTMLSelectElement} fileTypeTarget
 * @property {HTMLElement} documentModalDragDropContainerTarget
 * @property {HTMLButtonElement} submitBtnTarget
 *
 * @property {String[]} draggingClasses
 * @property {String[]} uploadDisabledClasses
 * @property {String[]} loadingClasses
 *
 * @property {DocumentForm[]} documentFormOutlets
 */
class BaseDocumentFormset extends Controller {
    static stores = [fileStore, globalFileTypeIndexStore, allowedExtensionsStore]

    static values = {
        state: { type: Number, default: DOCUMENT_STATE.IDLE },
        uploadDisabled: { type: Boolean, default: true },
        allowedExtensions: Object,
        nextUrl: { type: String, default: undefined },
        genericError: String,
    }
    static targets = [
        "errorContainer",
        "modal",
        "emptyFormTpl",
        "formsetContainer",
        "fileType",
        "allowedExtensions",
        "submitBtn",
        "documentModalDragDropContainer",
    ]
    static classes = ["uploadDisabled", "dragging", "loading"]
    static outlets = ["document-form"]

    initialize() {
        useStore(this)
    }

    getNextId() {
        if (this._currentId === undefined) {
            this._currentId = 0
        }
        return this._currentId++
    }

    /** @param {HTMLSelectElement} el */
    fileTypeTargetConnected(el) {
        el.dispatchEvent(new Event("change"))
    }

    allowedExtensionsValueChanged(value) {
        this.setAllowedExtensionsValue(value)
    }

    stateValueChanged(state) {
        this.modalTarget.classList.remove(...this.loadingClasses)
        this.submitBtnTarget.disabled = false
        this.errorContainerTarget.hidden = true

        if (state === DOCUMENT_STATE.LOADING) {
            this.modalTarget.classList.add(...this.loadingClasses)
            this.submitBtnTarget.disabled = true
        } else if (state === DOCUMENT_STATE.ERROR) {
            this.errorContainerTarget.hidden = false
        }
    }

    uploadDisabledValueChanged(value) {
        if (this.documentFormOutlets.length === 0) {
            this.submitBtnTarget.disabled = value
        } else {
            this.submitBtnTarget.disabled = false
        }
        if (value) {
            this.documentModalDragDropContainerTarget.classList.add(...this.uploadDisabledClasses)
        } else {
            this.documentModalDragDropContainerTarget.classList.remove(...this.uploadDisabledClasses)
        }
    }

    onChangeType({ target: { options, value } }) {
        this.uploadDisabledValue = value === ""
        const optionIdx = Math.max(
            Array.from(options).findIndex((option) => option.value === value),
            0,
        )
        this.setGlobalFileTypeIndexValue(optionIdx)
        this.allowedExtensionsTarget.textContent = this.allowedExtensionsValue[value || ""]
    }

    onDragEnter() {
        this.documentModalDragDropContainerTarget.classList.add(...this.draggingClasses)
    }

    onDragLeave() {
        this.documentModalDragDropContainerTarget.classList.remove(...this.draggingClasses)
    }

    /**
     * Do not remove; this is needed to allow the controller to receive `drop` events
     * https://developer.mozilla.org/en-US/docs/Web/API/HTMLElement/dragover_event#examples
     * @param {DragEvent} evt
     */
    onDragOver(evt) {
        evt.preventDefault()
        evt.stopPropagation()
    }

    /** @param {FileList} files */
    onDrop({ dataTransfer: { files } }) {
        this.processFiles(files)
    }

    /** @param {FileList} files */
    onFileSelect({ target: { files } }) {
        this.processFiles(files)
    }

    onModalClose() {
        this.errorContainerTarget.hidden = true
    }

    async onSubmit() {
        try {
            this.stateValue = DOCUMENT_STATE.LOADING

            let hasErrors = false
            const successFileNames = {}
            const promiseResults = await Promise.allSettled(
                this.documentFormOutlets.map((controller) => controller.submit()),
            )
            for (const promiseResult of promiseResults) {
                if (promiseResult.status === "fulfilled") {
                    successFileNames[promiseResult.value.pk] = promiseResult.value.documentName
                } else {
                    hasErrors = true
                }
            }

            this.dispatch(COMMON_EVENTS.DOCUMENT_SUCCESS, {
                detail: { [COMMON_EVENTS.DOCUMENT_SUCCESS]: successFileNames },
                target: window,
                prefix: "window",
            })

            if (hasErrors) {
                // Focus first erroneous field
                const autofocus = this.modalTarget.querySelector("[autofocus]")
                autofocus?.scrollIntoView({ block: "center" })
                autofocus?.focus({ focusVisible: true })
                throw FormValidationError
            }

            this.stateValue = DOCUMENT_STATE.IDLE
            this.dispatch(COMMON_EVENTS.ALL_DOCUMENTS_SUCCES, { target: window, prefix: "window" })
            requestAnimationFrame(() => {
                dsfr(this.modalTarget).modal.conceal()
            })
        } catch (_) {
            this.stateValue = DOCUMENT_STATE.ERROR
        }
    }

    /** @param {FileList} files */
    processFiles(files) {
        if (this.uploadDisabledValue) return

        for (const file of files) {
            const nextId = this.getNextId()
            this.setFilesValue((value) => ({ ...value, [nextId]: file }))
            this.formsetContainerTarget.insertAdjacentHTML(
                "beforeend",
                this.emptyFormTplTarget.innerHTML.replace("__file_id__", nextId),
            )
        }

        // Disable dragging style if needed
        this.onDragLeave()
    }
}

/**
 * @extends StorePropertiesType
 *
 * @property {HTMLElement} element
 * @property {Number} fileIdValue
 * @property {Number} stateValue
 * @property {String} deleteUrlValue
 * @property {HTMLFormElement} formTarget
 * @property {HTMLInputElement} documentFileTarget
 * @property {Boolean} hasDocumentFileTarget
 * @property {HTMLInputElement} documentNameTarget
 * @property {HTMLSelectElement} documentTypeTarget
 * @property {HTMLInputElement} inputIdTarget
 * @property {Boolean} hasInputIdTarget
 * @property {HTMLElement} accordionTitleTarget
 * @property {HTMLElement} accordionTypeLabelTarget
 * @property {HTMLElement} accordionContentTarget
 * @property {HTMLButtonElement} deleteBtnTarget
 * @property {HTMLTemplateElement} networkErrorTplTarget
 * @property {HTMLTemplateElement} serverErrorTplTarget
 * @property {String[]} loadingClasses
 * @property {String[]} deletingClasses
 * @property {String[]} successClasses
 * @property {String[]} errorClasses
 * @property {BaseDocumentFormset} documentFormsetOutlet
 */
class DocumentForm extends Controller {
    static stores = [fileStore, globalFileTypeIndexStore, allowedExtensionsStore]
    static values = {
        state: { type: Number, default: DOCUMENT_STATE.IDLE },
        fileId: { type: Number, default: -1 },
        deleteUrl: { type: String, default: "" },
    }
    static targets = [
        "form",
        "documentFile",
        "documentName",
        "documentType",
        "inputId",
        "accordionTitle",
        "accordionTypeLabel",
        "accordionContent",
        "deleteBtn",
        "networkErrorTpl",
        "serverErrorTpl",
        "erroneousField",
    ]
    static classes = ["loading", "deleting", "success", "error"]
    static outlets = ["document-formset"]

    initialize() {
        useStore(this)
        const dataAction = [
            this.element.dataset.action || "",
            `window:${COMMON_EVENTS.DOCUMENT_DELETE}@window->${this.identifier}#onDocumentRemoved`,
        ]
        this.element.dataset.action = dataAction.join(" ").trim()
        /** @type {AbortController | null} */
        this.abortController = null
    }

    stateValueChanged(state) {
        this.element.classList.remove(...this.loadingClasses, ...this.errorClasses, ...this.deletingClasses)
        this.deleteBtnTarget.disabled = false

        if (state === DOCUMENT_STATE.LOADING) {
            this.deleteBtnTarget.disabled = true
            this.element.classList.add(...this.loadingClasses)
        } else if (state === DOCUMENT_STATE.DELETING) {
            this.deleteBtnTarget.disabled = true
            this.element.classList.add(...this.deletingClasses)
        } else if (state === DOCUMENT_STATE.SUCCESS) {
            this.element.classList.add(...this.successClasses)
        } else if (state === DOCUMENT_STATE.ERROR) {
            this.element.classList.add(...this.errorClasses)
        }
    }

    /** @param {HTMLFormElement} form */
    formTargetConnected(form) {
        for (let element of form.elements) {
            const previousValue = element.dataset.action || ""
            element.dataset.action = `invalid->${this.identifier}#onInvalid ${previousValue}`
        }
    }

    /** @param {HTMLInputElement} el */
    documentFileTargetConnected(el) {
        if (this.fileIdValue >= 0) {
            const dataTransfer = new DataTransfer()
            dataTransfer.items.add(this.filesValue[this.fileIdValue])
            this.documentFileTarget.files = dataTransfer.files
        }
        el.dispatchEvent(new Event("input"))
    }

    /** @param {HTMLSelectElement} el */
    documentTypeTargetConnected(el) {
        if (el.value === "") {
            el.options[this.globalFileTypeIndexValue].selected = true
        }
        el.dispatchEvent(new Event("change"))
    }

    /** @param {HTMLInputElement} el */
    documentNameTargetConnected(el) {
        el.dispatchEvent(new Event("input"))
    }

    /**
     * @return {Promise<{pk: string, documentName: string}>}
     *          Returns the name and id of the document that was successfully uploaded.
     */
    async submit() {
        if (!this.formTarget.reportValidity()) throw FormValidationError()

        try {
            this.stateValue = DOCUMENT_STATE.LOADING
            this.abortController = new AbortController()
            /** @type {Response} */
            const result = await fetchPool(this.formTarget.action, {
                method: this.formTarget.method,
                body: new FormData(this.formTarget),
                redirect: "error",
                signal: this.abortController.signal,
            })

            if (result.ok || result.status === 400) {
                this.element.innerHTML = await result.text()
            }

            if (result.status === 500) {
                throw new ServerError()
            }

            if (result.ok) {
                this.stateValue = DOCUMENT_STATE.SUCCESS
                return {
                    pk: this.element.querySelector('[name="id"]').value,
                    documentName: escapeHTML(this.documentNameTarget.value.trim()),
                }
            } else {
                throw new FormValidationError()
            }
        } catch (e) {
            this.stateValue = DOCUMENT_STATE.ERROR
            if (!(e instanceof FormValidationError)) {
                console.error(e)
                // TypeError means the request never reach the backend
                // See https://developer.mozilla.org/en-US/docs/Web/API/Window/fetch#exceptions
                if (e instanceof TypeError) {
                    this.documentNameTarget.insertAdjacentHTML("afterend", this.networkErrorTplTarget.innerHTML)
                    this.documentNameTarget.closest(".fr-input-group").classList.add("fr-input-group--error")
                } else if (e instanceof ServerError) {
                    this.documentNameTarget.insertAdjacentHTML("afterend", this.serverErrorTplTarget.innerHTML)
                    this.documentNameTarget.closest(".fr-input-group").classList.add("fr-input-group--error")
                }
            }
            await this.#forceOpenAccordion()
            throw e
        } finally {
            this.abortController = null
        }
    }

    /** @param {Event} evt */
    async onInvalid(evt) {
        if (this.skipEvent === true) return
        evt.preventDefault()
        evt.stopPropagation()
        await Promise.all([
            dsfrDisclosePromise(dsfr(this.documentFormsetOutlet.modalTarget).modal),
            this.#forceOpenAccordion(),
        ])
        try {
            this.skipEvent = true
            let target = evt.target
            if (evt.target === this.documentFileTarget) {
                // Affect any file validation error to `[name="nom"]` field so it is visible
                this.documentNameTarget.setCustomValidity(evt.target.validationMessage)
                target = this.documentNameTarget
            }
            target.scrollIntoView({ block: "center" })
            target.reportValidity()
        } finally {
            this.skipEvent = false
        }
    }

    /** @param {FileList} files */
    onFileChanged({ target: { files } }) {
        if (this.documentNameTarget.value.trim() === "") {
            this.documentNameTarget.value = files.length === 0 ? "" : files[0].name
            this.documentNameTarget.dispatchEvent(new Event("input"))
        }
    }

    onDocumentRemoved({ detail }) {
        if (detail[COMMON_EVENTS.DOCUMENT_DELETE] === this.inputIdTarget.value) {
            this.element.remove()
        }
    }

    async onDelete() {
        try {
            this.stateValue = DOCUMENT_STATE.DELETING
            if (this.deleteUrlValue.length > 0) {
                this.abortController = new AbortController()
                await fetchPool(this.deleteUrlValue, { method: "POST" })
            }
            this.element.remove()
            this.dispatch(COMMON_EVENTS.DOCUMENT_DELETE, {
                detail: { [COMMON_EVENTS.DOCUMENT_DELETE]: this.inputIdTarget.value },
                target: window,
                prefix: "window",
            })
        } finally {
            this.stateValue = DOCUMENT_STATE.IDLE
            this.abortController = null
        }
    }

    onDocumentNameChanged({ target: { value } }) {
        this.accordionTitleTarget.textContent = value
    }

    onDocumentTypeChanged({ target: { value } }) {
        const option = Array.from(this.documentTypeTarget.options).find((option) => option.value === value)
        this.accordionTypeLabelTarget.textContent = option.textContent
        if (this.hasDocumentFileTarget) {
            this.documentFileTarget.accept = this.documentFormsetOutlet.allowedExtensionsValue[option.value]
        }
    }

    onModify() {
        if (this.accordionContentTarget.classList.contains("fr-collapse--expanded")) {
            dsfr(this.accordionContentTarget).collapse.conceal()
        } else {
            dsfr(this.accordionContentTarget).collapse.disclose()
        }
    }

    onModalClose() {
        if (!this.hasInputIdTarget) {
            this.abortController?.abort()
            this.element.remove()
        }
    }

    /** Just prevent submitting directly */
    async onSubmit(evt) {
        evt.preventDefault()
        evt.stopPropagation()
    }

    async #forceOpenAccordion() {
        await new Promise((resolve) => requestAnimationFrame(resolve))
        await dsfrDisclosePromise(dsfr(this.accordionContentTarget).collapse)
    }
}

export { DOCUMENT_FORM_ID, DOCUMENT_FORMSET_ID, DocumentForm, BaseDocumentFormset }
