import {applicationReady} from "Application"
import {Controller} from "Stimulus"

const DRAGGING_CLASS = "document-upload-drag-drop--dragging"

function getCookie(name) {
    const parts = `; ${document.cookie}`.split(`; ${name}=`)
    if (parts.length === 2) return parts.pop().split(";").shift()
}

/**
 * Dépôt d'un fichier CSV d'import en masse : affiche dans la modale le nombre de lignes
 * éligibles et ignorées renvoyé par le serveur, sans recharger la page.
 * @property {HTMLInputElement} fileTarget
 * @property {HTMLElement} fileNameTarget
 * @property {HTMLButtonElement} submitTarget
 * @property {HTMLElement} dropZoneTarget
 * @property {string} urlValue
 */
class ImportController extends Controller {
    static targets = ["file", "fileName", "submit", "dropZone", "result", "eligible", "ignored", "error", "errorText"]
    static values = {url: String}

    /** Do not remove; needed to allow the controller to receive `drop` events */
    onDragOver() {}

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
        this.errorTarget.hidden = true
    }

    async onSubmit() {
        const body = new FormData()
        body.append("file", this.fileTarget.files[0])

        this.submitTarget.disabled = true
        const response = await fetch(this.urlValue, {
            method: "POST",
            headers: {"X-CSRFToken": getCookie("csrftoken")},
            body,
        })
        const data = await response.json()
        this.submitTarget.disabled = false

        if (!response.ok) {
            this.errorTextTarget.textContent = data.error
            this.errorTarget.hidden = false
            return
        }
        this.eligibleTarget.textContent = data.eligible
        this.ignoredTarget.textContent = data.ignored
        this.resultTarget.hidden = false
    }
}

applicationReady.then(app => app.register("import", ImportController))
