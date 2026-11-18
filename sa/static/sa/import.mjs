import {applicationReady} from "Application"
import {Controller} from "Stimulus"

const DRAGGING_CLASS = "document-upload-drag-drop--dragging"

function getCookie(name) {
    const value = `; ${document.cookie}`
    const parts = value.split(`; ${name}=`)
    if (parts.length === 2) return parts.pop().split(";").shift()
}

class ImportController extends Controller {
    static targets = [
        "file",
        "fileName",
        "submit",
        "dropZone",
        "result",
        "eligible",
        "ignored",
        "errorText",
        "submitCreate",
        "done",
        "error",
        "resultCreation",
    ]
    static values = {url: String}

    /**
     * Do not remove; this is needed to allow the controller to receive `drop` events
     * https://developer.mozilla.org/en-US/docs/Web/API/HTMLElement/dragover_event#examples
     * @param {DragEvent} evt
     */
    onDragOver(evt) {
        evt.preventDefault()
        evt.stopPropagation()
    }

    onDragEnter() {
        this.dropZoneTarget.classList.add(DRAGGING_CLASS)
    }

    onDragLeave() {
        this.dropZoneTarget.classList.remove(DRAGGING_CLASS)
    }

    /** @param {DragEvent} evt */
    onDrop({dataTransfer: {files}}) {
        this.onDragLeave()
        this.fileTarget.files = files
        this.onFileSelect()
    }

    onFileSelect() {
        const file = this.fileTarget.files[0]
        this.fileNameTarget.textContent = file?.name ?? ""
        this.submitTarget.disabled = !file
        this.resultTarget.hidden = true
    }

    async onSubmit() {
        const body = new FormData()
        body.append("file", this.fileTarget.files[0])
        body.append("action", "test")

        this.submitTarget.disabled = true
        const response = await fetch(this.urlValue, {
            method: "POST",
            headers: {"X-CSRFToken": getCookie("csrftoken")},
            body,
        })
        const data = await response.json()
        this.submitTarget.disabled = false

        this.eligibleTarget.textContent = data.eligible
        this.ignoredTarget.textContent = data.ignored
        this.resultTarget.hidden = false
        this.submitCreateTarget.classList.remove("fr-hidden")
        this.submitTarget.classList.add("fr-hidden")
    }

    async onSubmitForCreation() {
        this.submitCreateTarget.disabled = true
        const body = new FormData()
        body.append("file", this.fileTarget.files[0])
        body.append("action", "create")

        this.submitTarget.disabled = true
        const response = await fetch(this.urlValue, {
            method: "POST",
            headers: {"X-CSRFToken": getCookie("csrftoken")},
            body,
        })
        const data = await response.json()
        this.doneTarget.textContent = data.done
        this.errorTarget.textContent = data.errors
        this.resultCreationTarget.classList.remove("fr-hidden")
        this.resultTarget.hidden = true
    }
}

applicationReady.then(app => app.register("import", ImportController))
