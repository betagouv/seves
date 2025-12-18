import {Controller} from "Stimulus"
import {BaseFormSetController} from "BaseFormset"
import {applicationReady} from "Application"
import {createStore, useStore} from "StimulusStore"


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
    constructor({file, title = "", validated = false}) {
        this.file = file
        this.title = title
        this.validated = validated
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
 * @property {Number} initialDocumentsValue
 * @property {Boolean} disabledValue
 * @property {HTMLDialogElement} modalTarget
 * @property {HTMLParagraphElement} documentsAddedMsgTarget
 * @property {HTMLSelectElement} globalFileTypeTarget
 * @property {HTMLElement} validatedSectionTarget
 * @property {HTMLTemplateElement} validatedSectionTplTarget
 * @property {HTMLElement} documentModalDragDropTarget
 * @property {HTMLInputElement} documentFileTarget
 * @property {HTMLTemplateElement} formTplTarget
 * @property {HTMLButtonElement} submitBtnTarget
 * @property {String[]} draggingClasses
 * @property {String[]} disabledClasses
 * @property {DocumentForm[]} documentFormOutlets
 */
class DocumentFormset extends BaseFormSetController {
    static stores = [fileStore, globalFileTypeIndexStore]
    static values = {disabled: {type: Boolean, default: true}, initialDocuments: {type: Number, default: 0}}
    static targets = [
        "modal",
        "documentsAddedMsg",
        "globalFileType",
        "validatedSection",
        "validatedSectionTpl",
        "submitBtn",
        "documentModalDragDrop",
        "documentFile",
        "formTpl"
    ]
    static classes = ["disabled", "dragging"]
    static outlets = ["document-form"]

    initialize() {
        useStore(this)
    }

    connect() {
        super.connect()
        this.globalFileTypeTarget.dispatchEvent(new Event("change"))
    }

    disabledValueChanged(value) {
        this.submitBtnTarget.disabled = value
        if(value) {
            this.documentModalDragDropTarget.classList.add(...this.disabledClasses)
        } else {
            this.documentModalDragDropTarget.classList.remove(...this.disabledClasses)
        }
    }

    onChangeType({target}) {
        this.disabledValue = target.value === ""
        this.setGlobalFileTypeIndexValue(
            Math.max(Array.from(target.options).findIndex(option => option.value === target.value), 0)
        )
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
        this.documentModalDragDropTarget.classList.add(...this.draggingClasses)
    }

    onDragLeave() {
        this.documentModalDragDropTarget.classList.remove(...this.draggingClasses)
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
        if(Object.keys(files).length + this.initialDocumentsValue === 0) {
            this.documentsAddedMsgTarget.innerText = "Aucun document ajouté"
        } else {
            this.documentsAddedMsgTarget.innerText = "Documents ajoutés au message"
        }
    }

    onModalClose() {
        // Remove files that were not validated
        let pristine = true
        for(const [id, {validated}] of Object.entries(this.filesValue)) {
            if(!validated) {
                delete this.filesValue[id]
                pristine = false
            }
        }
        if(!pristine) {
            // Unpacking dictionnary to force the creation of a new object to prevent
            // stimulus-store from optimizing-out notifying other controllers
            this.setFilesValue({...this.filesValue})
        }
    }

    onSubmit() {
        let pristine = true
        for(const [id, fileMeta] of Object.entries(this.filesValue)) {
            if(!fileMeta.validated) {
                this.validatedSectionTarget.insertAdjacentHTML(
                    "beforeend", this.validatedSectionTplTarget.innerHTML.replace("__fileId__", id)
                )
            }
            pristine = false
            fileMeta.validated = true
        }
        if(!pristine) {
            // Unpacking dictionnary to force the creation of a new object to prevent
            // stimulus-store from optimizing-out notifying other controllers
            this.setFilesValue({...this.filesValue})
        }
        dsfr(this.modalTarget).modal.conceal()
    }
}

/** @property {HTMLElement} titleTarget */
class ExistingDocumentValidated extends Controller {
    static targets = ["title"]

    onDelete() {
        this.element.remove()
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
 * @property {HTMLFormElement} formTarget
 * @property {HTMLInputElement} documentFileTarget
 * @property {HTMLElement} accordionTitleTarget
 * @property {HTMLElement} accordionTypeLabelTarget
 * @property {HTMLElement} accordionContentTarget
 * @property {HTMLInputElement} documentNameTarget
 * @property {HTMLOptionElement} documentTypeTarget
 * @property {String} fileIdValue
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
        "documentType"
    ]
    static values = {fileId: {type: String, default: ""}}

    initialize() {
        useStore(this)
    }

    /** @param {String} value */
    fileIdValueChanged(value) {
        if(value.length === 0 || this.filesValue[value] === undefined) return;

        const {file} = this.filesValue[value]
        const dataTransfer = new DataTransfer();
        dataTransfer.items.add(file)
        this.documentFileTarget.files = dataTransfer.files
        this.documentFileTarget.dispatchEvent(new Event("change"))

        // Updating form
        this.documentNameTarget.value = file.name
        this.documentNameTarget.dispatchEvent(new Event("input"))

        this.documentTypeTarget.item(this.globalFileTypeIndexValue).selected = true
        this.documentTypeTarget.dispatchEvent(new Event("change"))
    }

    /** @param {FileStoreStruct} files */
    onFilesUpdate(files) {
        if(!Object.hasOwn(files, this.fileIdValue)) {
            this.element.remove()
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
    app.register("existing-document-validated", ExistingDocumentValidated)
})
