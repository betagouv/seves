import {applicationReady, COMMON_EVENTS, escapeHTML} from "Application"
import {Controller} from "Stimulus"

/**
 * @property {HTMLElement} tabsTarget
 * @property {HTMLElement} documentsMessageContainerTarget
 * @property {HTMLTemplateElement} successMessageTplTarget
 */
class FicheBlocCommun extends Controller {
    static values = {tab: {type: String, default: ""}}
    static targets = ["tabs", "documentsMessageContainer", "successMessageTpl"]

    initialize() {
        const actions = [
            this.element.dataset.action || "",
            `window:${COMMON_EVENTS.DOCUMENT_SUCCESS}@window->${this.identifier}#onDocumentSuccess`,
            `window:${COMMON_EVENTS.ALL_DOCUMENTS_SUCCES}@window->${this.identifier}#onAllDocumentSuccess`,
        ]
        this.element.dataset.action = actions.join(" ").trim()

        for (const tab of this.tabsTarget.querySelectorAll(".fr-tabs__tab")) {
            const actions = [tab.dataset.action || "", `${this.identifier}#onTabSelected`]
            tab.dataset.action = actions.join(" ").trim()
        }
    }

    connect() {
        this.processDocumentSuccess()
        delete sessionStorage[COMMON_EVENTS.DOCUMENT_SUCCESS]
    }

    /** @param {HTMLElement} currentTarget */
    onTabSelected({currentTarget}) {
        const id = currentTarget.getAttribute("aria-controls")
        if (id && this.tabsTarget.querySelector(`#${id}`) !== null) {
            window.location.hash = `#${id}`
        }
    }

    /** @param {String} documentNamesJSON */
    onDocumentSuccess({detail}) {
        sessionStorage[COMMON_EVENTS.DOCUMENT_SUCCESS] = JSON.stringify(detail[COMMON_EVENTS.DOCUMENT_SUCCESS])
        this.processDocumentSuccess()
    }

    onAllDocumentSuccess() {
        window.location.reload()
    }

    processDocumentSuccess() {
        try {
            const names = JSON.parse(sessionStorage[COMMON_EVENTS.DOCUMENT_SUCCESS] || "{}")
            if (Object.keys(names).length === 0) return
            const html = Object.values(names)
                .map(documentName => `<li>${escapeHTML(documentName)}</li>`)
                .join("\n")
            this.documentsMessageContainerTarget.innerHTML = this.successMessageTplTarget.innerHTML.replace(
                "__html__",
                html,
            )
        } catch (_e) {
            delete sessionStorage[COMMON_EVENTS.DOCUMENT_SUCCESS]
        }
    }
}

applicationReady.then(app => app.register("fiche-bloc-commun", FicheBlocCommun))
