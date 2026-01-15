import {Controller} from "Stimulus"
import {BaseFormSetController} from "BaseFormset"
import {applicationReady} from "Application"
import {createStore, useStore} from "StimulusStore"
import {removeRequired} from "Forms"


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

/**
 * @property {File} file
 * @property {String} title
 * @property {Boolean} validated
 */
class FileMeta {
    constructor({file, title}) {
        this.file = file
        this.title = title
    }
}

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
 */

/**
 * @extends StorePropertiesType
 * @property {Boolean} disabledValue
 * @property {Object} allowedExtensionsPerDocumentTypeValue
 * @property {HTMLDialogElement} modalTarget
 * @property {HTMLParagraphElement} documentsAddedMsgTarget
 * @property {HTMLElement} allowedExtensionsTarget
 * @property {HTMLSelectElement} globalFileTypeTarget
 * @property {HTMLElement} validatedSectionTarget
 * @property {HTMLTemplateElement} validatedSectionTplTarget
 * @property {HTMLElement} documentModalDragDropContainerTarget
 * @property {HTMLInputElement} documentFileTarget
 * @property {HTMLTemplateElement} formTplTarget
 * @property {HTMLButtonElement} submitBtnTarget
 * @property {String[]} draggingClasses
 * @property {String[]} disabledClasses
 */
class DocumentFormset extends BaseFormSetController {
    static stores = [fileStore, globalFileTypeIndexStore]
    static values = {disabled: {type: Boolean, default: true}, allowedExtensionsPerDocumentType: Object}
    static targets = [
        "modal",
        "documentsAddedMsg",
        "allowedExtensions",
        "globalFileType",
        "validatedSection",
        "validatedSectionTpl",
        "submitBtn",
        "documentModalDragDropContainer",
        "documentFile",
        "formTpl"
    ]
    static classes = ["disabled", "dragging"]

    initialize() {
        /** @type {Set<string>} */
        this.cachedFileIds = new Set()
        useStore(this)
    }

    connect() {
        super.connect()
        this.globalFileTypeTarget.dispatchEvent(new Event("change"))
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
        const option = Math.max(Array.from(options).findIndex(option => option.value === value), 0)
        this.setGlobalFileTypeIndexValue(option)
        const allowedExtensions = this.allowedExtensionsPerDocumentTypeValue[option]
        if(allowedExtensions !== undefined) {
            this.allowedExtensionsTarget.textContent = allowedExtensions
        } else {
            this.allowedExtensionsTarget.textContent = this.allowedExtensionsPerDocumentTypeValue[""]
        }
    }

    /**
     * Return a new unique string ID.
     * @param {string[]} excludes Prevent generated ID to take one of these values
     * @return {string}
     */
    getId(excludes) {
        /* Just replace with crypto.randomUUID when adoption is 99% https://caniuse.com/mdn-api_crypto_randomuuid */
        if(typeof this._getId !== "function") {
            if(window.crypto && typeof window.crypto.randomUUID === "function") {
                this._getId = () => crypto.randomUUID()
            } else {
                this._getId = () => Math.floor(Math.random() * 2e16).toString(16)
            }
        }

        const _excludes = new Set(excludes)
        let newId = this._getId()
        while(_excludes.has(newId)) {
            newId = this._getId()
        }
        return newId
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

    /** @param {FileList} files */
    processFiles(files) {
        const newObjects = {}
        for(const file of files) {
            let id = this.getId(Object.keys(this.filesValue))
            newObjects[id] = new FileMeta({file})
            const newForm = this.onAddForm()
            newForm.setAttribute("data-document-form-file-id-value", id)
        }

        // Disable dragging style if needed
        this.onDragLeave()
        // Unpacking dictionnaries to force the creation of a new object to prevent
        // stimulus-store from optimizing-out notifying other controllers
        this.setFilesValue({...this.filesValue, ...newObjects})
    }

    /** @param {FileStoreStruct} files */
    onFilesUpdate(files) {
        const newKeys = new Set(Object.keys(files))

        if(newKeys.length) {
            this.documentsAddedMsgTarget.innerText = "Aucun document ajouté"
        } else {
            this.documentsAddedMsgTarget.innerText = "Documents ajoutés au message"
        }

        // Here we detect files for which we haven't yet created a card in validatedSectionTarget
        // It's necessary to do this here because files can from from both validating the modal and
        // DocumentForm adding an existing document for a draft message to the fileStore
        for(const id of newKeys.difference(this.cachedFileIds)) {
            this.validatedSectionTarget.insertAdjacentHTML(
                "beforeend", this.validatedSectionTplTarget.innerHTML.replace("__fileId__", id)
            )
        }

        this.cachedFileIds = newKeys
    }

    onModalClose() {
        this.onFilesUpdate(this.filesValue)
    }

    onSubmit() {
        dsfr(this.modalTarget).modal.conceal()
    }
}

/**
 * @extends StorePropertiesType
 * @property {String} fileIdValue
 * @property {HTMLElement} titleTarget
 */
class DocumentValidated extends Controller {
    static stores = [fileStore]
    static targets = ["title"]
    static values = {fileId: {type: String, default: ""}}

    initialize() {
        useStore(this)
    }

    connect() {
        this.titleTarget.textContent = this.filesValue[this.fileIdValue].title
    }

    onDelete() {
        delete this.filesValue[this.fileIdValue]
        // Unpacking dictionnary to force the creation of a new object to prevent
        // stimulus-store from optimizing-out notifying other controllers
        this.setFilesValue({...this.filesValue})
    }

    /** @param {FileStoreStruct} files */
    onFilesUpdate(files) {
        if(files[this.fileIdValue] === undefined) {
            this.element.remove()
        } else {
            this.titleTarget.textContent = files[this.fileIdValue].title
        }
    }
}

/**
 * @extends StorePropertiesType
 * @property {HTMLElement} element
 * @property {HTMLFormElement} formTarget
 * @property {HTMLInputElement} documentFileTarget
 * @property {Boolean} hasDocumentFileTarget
 * @property {HTMLElement} accordionTitleTarget
 * @property {HTMLElement} accordionTypeLabelTarget
 * @property {HTMLElement} accordionContentTarget
 * @property {HTMLInputElement} documentNameTarget
 * @property {HTMLOptionElement} documentTypeTarget
 * @property {HTMLInputElement} deleteTarget
 * @property {String} fileIdValue
 * @property {Boolean} initialValue
 */
class DocumentForm extends Controller {
    static stores = [fileStore, globalFileTypeIndexStore]
    static targets = [
        "form",
        "documentFile",
        "accordionTitle",
        "accordionTypeLabel",
        "accordionContent",
        "documentName",
        "documentType",
        "delete"
    ]
    static values = {fileId: {type: String, default: ""}, initial: {type: Boolean, default: false}}

    initialize() {
        useStore(this)
    }

    connect() {
        if(this.initialValue) {
            this.initFile()
        }
    }

    initFile() {
        const file = new File([], this.documentNameTarget.value)
        this.filesValue[this.fileIdValue] = new FileMeta({file, title: file.name})
        // Unpacking dictionnary to force the creation of a new object to prevent
        // stimulus-store from optimizing-out notifying other controllers
        this.setFilesValue({...this.filesValue})
        this.initialValue = false
    }

    /** @param {String} value */
    fileIdValueChanged(value) {
        // If this.initialValue === true, we're in the case of a document transmitted by the backend, this should be
        // processed in connect(); we're protecting this method in case it is triggered before connect()
        if(this.initialValue || value.length === 0 || this.filesValue[value] === undefined) return;

        const {file} = this.filesValue[value]
        if(this.hasDocumentFileTarget) {
            const dataTransfer = new DataTransfer();
            dataTransfer.items.add(file)
            this.documentFileTarget.files = dataTransfer.files
            this.documentFileTarget.dispatchEvent(new Event("change"))
        }
        this.updateForm(file)
    }

    /** @param {File} file */
    updateForm(file) {
        this.documentNameTarget.value = file.name
        this.documentNameTarget.dispatchEvent(new Event("input"))

        this.documentTypeTarget.item(this.globalFileTypeIndexValue).selected = true
        this.documentTypeTarget.dispatchEvent(new Event("change"))
    }

    /** @param {FileStoreStruct} files */
    onFilesUpdate(files) {
        if(!this.initialValue && files[this.fileIdValue] === undefined) {
            // Don't remove the form as it would not be process by the formset. Instead, disabled and hide it
            removeRequired(this.element)
            this.deleteTarget.value = "on"
            this.element.setAttribute("hidden", "hidden")
            delete this.element.dataset.controller
        }
    }

    onDocumentNameChanged({target: {value}}) {
        this.filesValue[this.fileIdValue].title = value
        this.accordionTitleTarget.textContent = value
    }

    onDocumentTypeChanged({target: {value}}) {
        this.accordionTypeLabelTarget.textContent = Array.from(this.documentTypeTarget.options).find(
            option => option.value === value
        ).textContent
    }

    onModify() {
        if(this.accordionContentTarget.classList.contains("fr-collapse--expanded")) {
            dsfr(this.accordionContentTarget).collapse.conceal()
        } else {
            dsfr(this.accordionContentTarget).collapse.disclose()
        }
    }

    onDelete() {
        delete this.filesValue[this.fileIdValue]
        // Unpacking dictionnary to force the creation of a new object to prevent
        // stimulus-store from optimizing-out notifying other controllers
        this.setFilesValue({...this.filesValue})
    }
}

applicationReady.then(app => {
    app.register("document-formset", DocumentFormset)
    app.register("document-form", DocumentForm)
    app.register("document-validated", DocumentValidated)
})
