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
        "submitCreate",
        "done",
        "errorCount",
        "resultCreation",
        "error",
        "errorText",
        "description",
        "read",
        "errorDetails",
        "errorDetailsContent",
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
        this.submitTarget.classList.remove("fr-hidden")
        this.submitCreateTarget.disabled = false
        this.submitCreateTarget.classList.add("fr-hidden")
        this.resultTarget.classList.add("fr-hidden")
        this.resultCreationTarget.classList.add("fr-hidden")
        this.errorTarget.classList.add("fr-hidden")
    }

    async getData(response) {
        const data = await response.json().catch(() => ({}))
        if (response.ok) return data
        this.errorTextTarget.textContent = data.error ?? "Une erreur est survenue lors du traitement du fichier."
        this.errorTarget.classList.remove("fr-hidden")
    }

    showErrorTable(errors) {
        this.errorDetailsTarget.classList.remove("fr-hidden")
        for (const error of errors) {
            const html = `<tr>
               <td>${error.line}</td>
               <td>${error.id}</td>
               <td>${error.field}</td>
               <td>${error.value}</td>
               <td>${error.message}</td>
            </tr>`

            this.errorDetailsContentTarget.insertAdjacentHTML("beforeend", html)
        }
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
        this.submitTarget.disabled = false

        const data = await this.getData(response)
        if (!data) return

        this.eligibleTarget.textContent = data.eligible
        this.ignoredTarget.textContent = data.ignored
        this.readTarget.textContent = data.read
        this.resultTarget.classList.remove("fr-hidden")
        this.submitCreateTarget.classList.remove("fr-hidden")
        this.submitTarget.classList.add("fr-hidden")
        this.dropZoneTarget.classList.add("fr-hidden")
        this.descriptionTarget.classList.remove("fr-hidden")
        this.showErrorTable(data.errors)
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
        const data = await this.getData(response)
        if (!data) {
            this.submitCreateTarget.disabled = false
            return
        }

        this.doneTarget.textContent = data.done
        this.errorCountTarget.textContent = data.errors
        this.resultCreationTarget.classList.remove("fr-hidden")
        this.resultTarget.classList.add("fr-hidden")
    }
}

applicationReady.then(app => app.register("import", ImportController))
