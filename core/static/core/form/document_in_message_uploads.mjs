import {Controller} from "Stimulus"
import {BaseFormSetController} from "BaseFormset"
import {applicationReady} from "Application"
import {useStore, createStore} from "StimulusStore"


const fileTypeStore = createStore({
    name: "fileType",
    type: String,
    initialValue: "",
});
const fileStore = createStore({
    name: "files",
    type: Object,
    initialValue: {},
});

/**
 * @typedef {Object} StorePropertiesType
 * @property {Object<String, File>} filesValue
 * @property {import("StimulusStore/dist/types/updateMethod").UpdateMethod} setFilesValue
 * @property {function(Object<String, File>): undefined} onFilesUpdate
 * @property {String} fileTypeValue
 * @property {import("StimulusStore/dist/types/updateMethod").UpdateMethod} setFileTypeValue
 * @property {function(String): undefined} onFileTypeUodate
 */

/**
 * @extends StorePropertiesType
 * @property {HTMLElement} documentModalDragDropTarget
 * @property {HTMLTemplateElement} formTplTarget
 * @property {String} draggingClass
 */
class DocumentFormset extends BaseFormSetController {
    static stores = [fileStore, fileTypeStore]
    static targets = ["documentModalDragDrop", "formTpl"]
    static classes = ["dragging"]

    initialize() {
        useStore(this)
    }

    onChangeType({target: {value}}) {
        this.setFileTypeValue(value)
        if(value === "") {
            this.documentModalDragDropTarget.setAttribute("disabled", "true")
        } else {
            this.documentModalDragDropTarget.removeAttribute("disabled")
        }
    }

    /**
     * Return a     new unique string ID using crypto.randomUUID and defaulting to a manual algorithm on brwosers
     * not implementing the Crypto API. Just replace with crypto.randomUUID when adoption is 99%
     * https://caniuse.com/mdn-api_crypto_randomuuid
     * @return {string}
     */
    getId() {
        try {
            return crypto.randomUUID()
        } catch(_) {
            Math.floor(Math.random() * 2e16).toString(16)
        }
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

    /** @param {DragEvent} evt */
    onDragEnter(evt) {
        this.documentModalDragDropTarget.classList.add(this.draggingClass)
    }

    /** @param {DragEvent} evt */
    onDragLeave(evt) {
        this.documentModalDragDropTarget.classList.remove(this.draggingClass)
    }

    /** @param {FileList} files */
    onDrop({dataTransfer: {files}}) {
        const newFiles = {}

        for(const file of files) {
            const id = this.getId()
            newFiles[id] = file
            const newForm = this.onAddForm()
            newForm.setAttribute("data-document-form-file-id-value", id)
        }

        this.setFilesValue(previousValue => { return {...previousValue, ...newFiles} })
    }
}

/**
 * @extends StorePropertiesType
 * @property {HTMLInputElement} documentFileTarget
 * @property {String} fileIdValue
 */
class DocumentForm extends Controller {
    static stores = [fileStore, fileTypeStore]
    static targets = ["documentFile"]
    static values = {fileId: {type: String, default: ""}}

    initialize() {
        useStore(this)
    }


    onFilesUpdate(value) {

    }


    onFileTypeUodate(value) {

    }

    /** @param {String} value */
    fileIdValueChanged(value) {
        if(value.length === 0 || this.filesValue === undefined) return;

        const file = this.filesValue[value]
        if(file instanceof File) {
            debugger
            const dataTransfer = new DataTransfer();
            dataTransfer.items.add(file)
            this.documentFileTarget.files = dataTransfer.files
        }
    }
}

applicationReady.then(app => {
    app.register("document-formset", DocumentFormset)
    app.register("document-form", DocumentForm)
})
