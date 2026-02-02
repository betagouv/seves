import {Controller} from "Stimulus"
import {applicationReady, dsfrDisclosePromise, fetchPool} from "Application"
import {createStore, useStore} from "StimulusStore"


const DOCUMENT_FORM_ID = "document-form"
const DOCUMENT_FORMSET_ID = "document-formset"
const STORAGE_DOCUMENT_SUCCESS = "STORAGE_DOCUMENT_SUCCESS"

const DOCUMENT_STATE = Object.freeze({
    IDLE: 1,
    LOADING: 2,
    ERROR: 3,
})

const globalFileTypeIndexStore = createStore({
    name: "globalFileTypeIndex",
    type: Number,
    initialValue: 0,
});

const fileStore = createStore({
    name: "files",
    type: Object,
    initialValue: {},
});

const allowedExtensionsStore = createStore({
    name: "allowedExtensions",
    type: Object,
    initialValue: {},
});

const FormValidationError = Error("invalid")

/** @typedef {Object<String, FileMeta>} FileStoreStruct */

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
 * @property {HTMLTemplateElement} successMessageTplTarget
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
class DocumentFormset extends Controller {
    static stores = [fileStore, globalFileTypeIndexStore, allowedExtensionsStore]

    static values = {
        state: {type: Number, default: DOCUMENT_STATE.IDLE},
        uploadDisabled: {type: Boolean, default: true},
        allowedExtensions: Object,
        nextUrl: String,
        genericError: String
    }
    static targets = [
        "successMessageTpl",
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

    get messagesContainer() {
        return document.querySelector("#tabpanel-documents-panel .document-messages")
    }

    initialize() {
        useStore(this)
    }

    connect() {
        this.processSuccessMessages()
        delete sessionStorage[STORAGE_DOCUMENT_SUCCESS]
    }

    getNextId() {
        if(this._currentId === undefined) {
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

        if(state === DOCUMENT_STATE.LOADING) {
            this.modalTarget.classList.add(...this.loadingClasses)
            this.submitBtnTarget.disabled = true
        } else if(state === DOCUMENT_STATE.ERROR) {
            this.errorContainerTarget.hidden = false
        }
    }

    uploadDisabledValueChanged(value) {
        if(this.documentFormOutlets.length === 0) {
            this.submitBtnTarget.disabled = value
        } else {
            this.submitBtnTarget.disabled = false
        }
        if(value) {
            this.documentModalDragDropContainerTarget.classList.add(...this.uploadDisabledClasses)
        } else {
            this.documentModalDragDropContainerTarget.classList.remove(...this.uploadDisabledClasses)
        }
    }

    onChangeType({target: {options, value}}) {
        this.uploadDisabledValue = value === ""
        const optionIdx = Math.max(Array.from(options).findIndex(option => option.value === value), 0)
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
    onDrop({dataTransfer: {files}}) {
        this.processFiles(files)
    }

    /** @param {FileList} files */
    onFileSelect({target: {files}}) {
        this.processFiles(files)
    }

    onModalClose() {
        this.formsetContainerTarget.innerHTML = ""
        this.errorContainerTarget.hidden = true
        this.processSuccessMessages()
    }

    async onSubmit() {
        try {
            this.stateValue = DOCUMENT_STATE.LOADING

            let hasErrors = false
            let successMessage = ""
            const promiseResults = await Promise.allSettled(this.documentFormOutlets.map(controller => controller.submit()))
            for(const promiseResult of promiseResults) {
                if(promiseResult.status === "fulfilled") {
                    successMessage = `${successMessage}<li>${promiseResult.value}</li>`
                } else {
                    hasErrors = true
                }
            }

            sessionStorage[STORAGE_DOCUMENT_SUCCESS] = successMessage

            if(hasErrors) {
                throw FormValidationError
            }

            this.stateValue = DOCUMENT_STATE.IDLE

            // Redirect only if all requests where successful
            const nextURL = URL.parse(this.nextUrlValue, window.location.origin)
            window.location.href = this.nextUrlValue
            dsfr(this.modalTarget).modal.conceal()
            if(nextURL.pathname === window.location.pathname) {
                // Force reload if we're on the same path otherwise browser won't trigger an HTTP query
                window.location.reload()
            }
        } catch(_) {
            this.stateValue = DOCUMENT_STATE.ERROR
        }
    }

    /** @param {FileList} files */
    processFiles(files) {
        if(this.uploadDisabledValue) return;

        for(const file of files) {
            const nextId = this.getNextId()
            this.setFilesValue(value => ({...value, [nextId]: file}))
            this.formsetContainerTarget.insertAdjacentHTML(
                "beforeend",
                this.emptyFormTplTarget.innerHTML.replace("__file_id__", nextId)
            )
        }

        // Disable dragging style if needed
        this.onDragLeave()
    }

    processSuccessMessages() {
        const html = sessionStorage[STORAGE_DOCUMENT_SUCCESS]
        if((typeof html) == "string" && html.length > 0) {
            this.messagesContainer.innerHTML = this.successMessageTplTarget.innerHTML.replace("__html__", html)
        }
    }
}

/**
 * @extends StorePropertiesType
 *
 * @property {HTMLElement} element
 * @property {Number} fileIdValue
 * @property {Number} stateValue
 * @property {HTMLFormElement} formTarget
 * @property {HTMLInputElement} documentFileTarget
 * @property {Boolean} hasDocumentFileTarget
 * @property {HTMLInputElement} documentNameTarget
 * @property {HTMLSelectElement} documentTypeTarget
 * @property {HTMLElement} accordionTitleTarget
 * @property {HTMLElement} accordionTypeLabelTarget
 * @property {HTMLElement} accordionContentTarget
 * @property {HTMLTemplateElement} networkErrorTplTarget
 * @property {String[]} loadingClasses
 * @property {String[]} errorClasses
 * @property {DocumentFormset} documentFormsetOutlet
 */
class DocumentForm extends Controller {
    static stores = [fileStore, globalFileTypeIndexStore, allowedExtensionsStore]
    static values = {
        fileId: {type: Number, default: -1},
        state: {type: Number, default: DOCUMENT_STATE.IDLE},
    }
    static targets = [
        "form",
        "documentFile",
        "documentName",
        "documentType",
        "accordionTitle",
        "accordionTypeLabel",
        "accordionContent",
        "networkErrorTpl"
    ]
    static classes = ["loading", "error"]
    static outlets = ["document-formset"]

    initialize() {
        useStore(this)
    }

    stateValueChanged(state) {
        this.element.classList.remove(...this.loadingClasses, ...this.errorClasses)
        if(state === DOCUMENT_STATE.LOADING) {
            this.element.classList.add(...this.loadingClasses)
        } else if(state === DOCUMENT_STATE.ERROR) {
            this.element.classList.add(...this.errorClasses)
        }
    }

    /** @param {HTMLFormElement} form */
    formTargetConnected(form) {
        for(let element of form.elements) {
            const previousValue = element.dataset.action || ""
            element.dataset.action = `invalid->${this.identifier}#onInvalid ${previousValue}`
        }
    }

    /** @param {HTMLInputElement} el */
    documentFileTargetConnected(el) {
        if(this.fileIdValue >= 0) {
            const dataTransfer = new DataTransfer();
            dataTransfer.items.add(this.filesValue[this.fileIdValue])
            this.documentFileTarget.files = dataTransfer.files
        }
        el.dispatchEvent(new Event("input"))
    }

    /** @param {HTMLSelectElement} el */
    documentTypeTargetConnected(el) {
        if(el.value === "") {
            el.options[this.globalFileTypeIndexValue].selected = true
        }
        el.dispatchEvent(new Event("change"))
    }

    /** @param {HTMLInputElement} el */
    documentNameTargetConnected(el) {
        el.dispatchEvent(new Event("input"))
    }

    /** @return {Promise<string>} Returns the name of the document that was successfully uploaded */
    async submit() {
        if(!this.formTarget.reportValidity()) throw FormValidationError

        try {
            this.stateValue = DOCUMENT_STATE.LOADING
            /** @type {Response} */
            const result = await fetchPool(
                this.formTarget.action,
                {method: this.formTarget.method, body: new FormData(this.formTarget)}
            )

            if(result.ok || result.status === 400) {
                this.element.innerHTML = await result.text()
            }

            if(result.ok) {
                this.stateValue = DOCUMENT_STATE.IDLE
                return this.documentNameTarget.value.trim()
            } else {
                throw FormValidationError
            }
        } catch(e) {
            this.stateValue = DOCUMENT_STATE.ERROR
            if(e !== FormValidationError) {
                console.error(e)
                // TypeError means the request never reach the backend
                // See https://developer.mozilla.org/en-US/docs/Web/API/Window/fetch#exceptions
                if(e instanceof TypeError) {
                    this.documentNameTarget.insertAdjacentHTML("afterend", this.networkErrorTplTarget.innerHTML)
                    this.documentNameTarget.closest(".fr-input-group").classList.add("fr-input-group--error")
                }
            }
            throw e
        }
    }

    /** @param {Event} evt */
    async onInvalid(evt) {
        if(this.skipEvent === true) return;
        evt.preventDefault()
        evt.stopPropagation()
        debugger
        await Promise.all([
            dsfrDisclosePromise(dsfr(this.documentFormsetOutlet.modalTarget).modal),
            dsfrDisclosePromise(dsfr(this.accordionContentTarget).collapse),
        ])
        try {
            this.skipEvent = true
            let target = evt.target
            if(evt.target === this.documentFileTarget) {
                // Affect any file validation error to `[name="nom"]` field so it is visible
                this.documentNameTarget.setCustomValidity(evt.target.validationMessage)
                target = this.documentNameTarget
            }
            target.scrollIntoView({block: "center"})
            target.reportValidity()
        } finally {
            this.skipEvent = false
        }
    }

    /** @param {FileList} files */
    onFileChanged({target: {files}}) {
        if(this.documentNameTarget.value.trim() === "") {
            this.documentNameTarget.value = files.length === 0 ? "" : files[0].name
            this.documentNameTarget.dispatchEvent(new Event("input"))
        }
    }

    onDelete() {
        this.element.remove()
    }

    onDocumentNameChanged({target: {value}}) {
        this.accordionTitleTarget.textContent = value
    }

    onDocumentTypeChanged({target: {value}}) {
        const option = Array.from(this.documentTypeTarget.options).find(
            option => option.value === value
        )
        this.accordionTypeLabelTarget.textContent = option.textContent
        if(this.hasDocumentFileTarget) {
            this.documentFileTarget.accept = this.documentFormsetOutlet.allowedExtensionsValue[option.value]
        }
    }

    onModify() {
        if(this.accordionContentTarget.classList.contains("fr-collapse--expanded")) {
            dsfr(this.accordionContentTarget).collapse.conceal()
        } else {
            dsfr(this.accordionContentTarget).collapse.disclose()
        }
    }

    /** Just prevent submitting directly */
    async onSubmit(evt) {
        evt.preventDefault()
        evt.stopPropagation()
    }
}

applicationReady.then(app => {
    app.register(DOCUMENT_FORMSET_ID, DocumentFormset)
    app.register(DOCUMENT_FORM_ID, DocumentForm)
})
