import {Controller} from "Stimulus"
import {applicationReady, dsfrDisclosePromise, fetchPool} from "Application"
import {createStore, useStore} from "StimulusStore"


const DOCUMENT_FORM_ID = "document-form"
const DOCUMENT_FORMSET_ID = "document-formset"
const LOCAL_STORAGE_MESSAGES_KEY = "document-formset-messages"

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
 * @property {Boolean} disabledValue
 * @property {Object} allowedExtensionsValue
 * @property {String} nextUrlValue
 *
 * @property {HTMLDialogElement} modalTarget
 * @property {HTMLTemplateElement} emptyFormTplTarget
 * @property {HTMLElement} formsetContainerTarget
 * @property {HTMLElement} allowedExtensionsTarget
 * @property {HTMLSelectElement} fileTypeTarget
 * @property {HTMLElement} documentModalDragDropContainerTarget
 * @property {HTMLButtonElement} submitBtnTarget
 *
 * @property {String[]} draggingClasses
 * @property {String[]} disabledClasses
 * @property {String[]} loadingClasses
 *
 * @property {DocumentForm[]} documentFormOutlets
 */
class DocumentFormset extends Controller {
    static stores = [fileStore, globalFileTypeIndexStore, allowedExtensionsStore]

    static values = {
        disabled: {type: Boolean, default: true},
        allowedExtensions: Object,
        nextUrl: String,
    }
    static targets = [
        "modal",
        "emptyFormTpl",
        "formsetContainer",
        "fileType",
        "allowedExtensions",
        "submitBtn",
        "documentModalDragDropContainer",
    ]
    static classes = ["disabled", "dragging", "loading"]
    static outlets = ["document-form"]

    initialize() {
        useStore(this)
    }

    connect() {
        document.querySelector("#tabpanel-documents-panel .document-messages").insertAdjacentHTML(
            "beforeend", localStorage.getItem(LOCAL_STORAGE_MESSAGES_KEY) || ""
        )
        localStorage.removeItem(LOCAL_STORAGE_MESSAGES_KEY)
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

    disabledValueChanged(value) {
        this.submitBtnTarget.disabled = value
        if(value) {
            this.documentModalDragDropContainerTarget.classList.add(...this.disabledClasses)
        } else {
            this.documentModalDragDropContainerTarget.classList.remove(...this.disabledClasses)
        }
    }

    onChangeType({target: {options, value}}) {
        this.disabledValue = value === ""
        const optionIdx = Math.max(Array.from(options).findIndex(option => option.value === value), 0)
        this.setGlobalFileTypeIndexValue(optionIdx)
        this.allowedExtensionsTarget.textContent = this.allowedExtensionsValue[optionIdx] || ""
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
    }

    async onSubmit() {
        try {
            this.disabledValue = true
            this.modalTarget.classList.add(...this.loadingClasses)
            const statusCodes = await Promise.all(this.documentFormOutlets.map(controller => controller.submit()))

            // Redirect only if all requests where successful
            if(statusCodes.filter(status => status < 200 || status >= 300).length === 0) {
                const nextURL = URL.parse(this.nextUrlValue, window.location.origin)
                window.location.href = this.nextUrlValue
                dsfr(this.modalTarget).modal.conceal()
                if(nextURL.pathname === window.location.pathname) {
                    // Force reload if we're on the same path otherwise browser won't trigger an HTTP query
                    window.location.reload()
                }
            }
        } catch(_) {
            /* Do nothing */
        } finally {
            this.disabledValue = false
            this.modalTarget.classList.remove(...this.loadingClasses)
        }
    }

    /** @param {FileList} files */
    processFiles(files) {
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
}

/**
 * @extends StorePropertiesType
 *
 * @property {HTMLElement} element
 * @property {Number} fileIdValue
 * @property {HTMLElement} errorContainerTarget
 * @property {HTMLTemplateElement} errorTplTarget
 * @property {HTMLFormElement} formTarget
 * @property {HTMLInputElement} documentFileTarget
 * @property {Boolean} hasDocumentFileTarget
 * @property {HTMLInputElement} documentNameTarget
 * @property {HTMLSelectElement} documentTypeTarget
 * @property {HTMLElement} accordionTitleTarget
 * @property {HTMLElement} accordionTypeLabelTarget
 * @property {HTMLElement} accordionContentTarget
 * @property {HTMLInputElement} deleteTarget
 * @property {HTMLElement} successMessageTarget
 * @property {String[]} loadingClasses
 */
class DocumentForm extends Controller {
    static stores = [fileStore, globalFileTypeIndexStore, allowedExtensionsStore]
    static values = {fileId: {type: Number, default: -1}}
    static targets = [
        "errorContainer",
        "errorTpl",
        "form",
        "documentFile",
        "documentName",
        "documentType",
        "accordionTitle",
        "accordionTypeLabel",
        "accordionContent",
        "delete",
    ]
    static classes = ["loading"]

    /** @return {DocumentFormset} */
    get formset() {
        if(this._formset === undefined) {
            this._formset = this.application.getControllerForElementAndIdentifier(
                document.querySelector(`[data-controller="${DOCUMENT_FORMSET_ID}"]`), DOCUMENT_FORMSET_ID
            )
        }

        return this._formset
    }

    initialize() {
        useStore(this)
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

    async submit() {
        if(!this.formTarget.reportValidity()) throw "invalid"

        try {
            this.element.classList.add(...this.loadingClasses)
            /** @type {Response} */
            const result = await fetchPool(
                this.formTarget.action,
                {method: this.formTarget.method, body: new FormData(this.formTarget)}
            )
            if(result.ok || result.status === 400) {
                const tmpNode = document.createElement("div")
                tmpNode.innerHTML = await result.text()
                this.element.innerHTML = tmpNode.querySelector(`[data-controller="${this.identifier}"]`).innerHTML

                // Storing messages until reload
                for(const msgNode of tmpNode.querySelectorAll(".document-messages")) {
                    const previous = localStorage.getItem(LOCAL_STORAGE_MESSAGES_KEY) || ""
                    localStorage.setItem(LOCAL_STORAGE_MESSAGES_KEY, previous + msgNode.innerHTML)
                    msgNode.remove()
                }
            }
            return result.status
        } catch(e) {
            console.error(e)
            this.errorContainerTarget.innerHTML = this.errorTplTarget.innerHTML.replace(
                "__error__", "Il y a eu un problème réseau lors de la soumission du document ; veuillez réessayer."
            )
            throw e
        } finally {
            this.element.classList.remove(...this.loadingClasses)
        }
    }

    /** @param {Event} evt */
    async onInvalid(evt) {
        if(this.skipEvent === true) return;
        evt.preventDefault()
        evt.stopPropagation()
        await Promise.all([
            dsfrDisclosePromise(dsfr(this.formset.modalTarget).modal),
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
            this.documentFileTarget.accept = this.formset.allowedExtensionsValue[option.value]
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
