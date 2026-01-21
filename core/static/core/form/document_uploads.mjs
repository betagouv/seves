import {Controller} from "Stimulus"
import {applicationReady, dsfrDisclosePromise, fetchPool} from "Application"


const DOCUMENT_FORM_ID = "document-form"
const DOCUMENT_FORMSET_ID = "document-formset"
const LOCAL_STORAGE_MESSAGES_KEY = "document-formset-messages"

/**
 * @property {Boolean} disabledValue
 * @property {Number} fileTypeIdxValue
 * @property {Object} allowedExtensionsPerDocumentTypeValue
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
    static values = {
        disabled: {type: Boolean, default: true},
        fileTypeIdx: Number,
        allowedExtensionsPerDocumentType: Object,
        nextUrl: String,
    }
    static targets = [
        "modal",
        "emptyFormTpl",
        "formsetContainer",
        "fileType",
        "fileTypeIdx",
        "allowedExtensions",
        "submitBtn",
        "documentModalDragDropContainer",
    ]
    static classes = ["disabled", "dragging", "loading"]
    static outlets = ["document-form"]

    connect() {
        this.fileTypeTarget.dispatchEvent(new Event("change"))
        this.cachedContainer = document.createElement("div")

        document.querySelector("#tabpanel-documents-panel .document-messages").insertAdjacentHTML(
            "beforeend", localStorage.getItem(LOCAL_STORAGE_MESSAGES_KEY) || ""
        )
        localStorage.removeItem(LOCAL_STORAGE_MESSAGES_KEY)
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
        const allowedExtensions = this.allowedExtensionsPerDocumentTypeValue[optionIdx]
        if(allowedExtensions !== undefined) {
            this.allowedExtensionsTarget.textContent = allowedExtensions
        } else {
            this.allowedExtensionsTarget.textContent = this.allowedExtensionsPerDocumentTypeValue[""]
        }
        this.fileTypeIdxValue = optionIdx
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
            this.submitBtnTarget.disabled = true
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
        } finally {
            this.submitBtnTarget.disabled = false
            this.modalTarget.classList.remove(...this.loadingClasses)
        }
    }

    /** @param {FileList} files */
    processFiles(files) {
        for(const file of files) {
            this.cachedContainer.innerHTML = this.emptyFormTplTarget.innerHTML

            /** @type {HTMLSelectElement} */
            const documentTypeNode = this.cachedContainer.querySelector('[name$="document_type"]')
            documentTypeNode.options[this.fileTypeIdxValue].selected = true

            /** @type {HTMLInputElement} */
            const fileNode = this.cachedContainer.querySelector('[name$="file"]')
            const dataTransfer = new DataTransfer();
            dataTransfer.items.add(file)
            fileNode.files = dataTransfer.files

            for(const child of this.cachedContainer.children) {
                this.formsetContainerTarget.insertAdjacentElement("beforeend", child)
            }
        }

        // Disable dragging style if needed
        this.onDragLeave()
    }
}

/**
 * @property {HTMLElement} element
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
    static targets = [
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

    /** @param {HTMLFormElement} form */
    formTargetConnected(form) {
        for(let element of form.elements) {
            const previousValue = element.dataset.action || ""
            element.dataset.action = `invalid->${this.identifier}#onInvalid ${previousValue}`
        }
    }

    documentFileTargetConnected(el) {
        if(this.cachedFileList !== undefined) {
            // Silently update the file to not trigger a name change
            el.files = this.cachedFileList
            delete this.cachedFileList
        } else {
            el.dispatchEvent(new Event("input"))
        }
    }

    documentTypeTargetConnected(el) {
        el.dispatchEvent(new Event("change"))
    }

    documentNameTargetConnected(el) {
        el.dispatchEvent(new Event("input"))
    }

    async submit() {
        if(!this.formTarget.reportValidity()) return;
        try {
            this.element.classList.add(...this.loadingClasses)
            /** @type {Response} */
            const result = await fetchPool(
                this.formTarget.action,
                {method: this.formTarget.method, body: new FormData(this.formTarget)}
            )
            if(result.ok || result.status === 400) {
                this.cachedFileList = this.documentFileTarget.files
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
        this.skipEvent = true
        if(evt.target === this.documentFileTarget) {
            // Affect any validation error form file to name field so it is visible
            this.documentNameTarget.setCustomValidity(evt.target.validationMessage)
            this.documentNameTarget.reportValidity()
        } else {
            evt.target.scrollIntoView({block: "center"})
            evt.target.reportValidity()
        }
        this.skipEvent = false
    }

    /** @param {FileList} files */
    onFileChanged({target: {files}}) {
        this.documentNameTarget.value = files.length === 0 ? "" : files[0].name
        this.documentNameTarget.dispatchEvent(new Event("input"))
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
            this.documentFileTarget.accept = this.formset.allowedExtensionsPerDocumentTypeValue[option.value]
        }
    }

    onModify() {
        if(this.accordionContentTarget.classList.contains("fr-collapse--expanded")) {
            dsfr(this.accordionContentTarget).collapse.conceal()
        } else {
            dsfr(this.accordionContentTarget).collapse.disclose()
        }
    }

    /** Just prevent submitting directly*/
    async onSubmit(evt) {
        evt.preventDefault()
        evt.stopPropagation()
    }
}

applicationReady.then(app => {
    app.register(DOCUMENT_FORMSET_ID, DocumentFormset)
    app.register(DOCUMENT_FORM_ID, DocumentForm)
})
