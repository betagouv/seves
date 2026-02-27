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
    }

    tabsTargetConnected(tabsTarget) {
        this.#tryInitTabs()
        const actions = [tabsTarget.dataset.action || "", `dsfr.current->${this.identifier}#onTabSelected`]
        tabsTarget.dataset.action = actions.join(" ").trim()
    }

    connect() {
        this.processDocumentSuccess()
        delete sessionStorage[COMMON_EVENTS.DOCUMENT_SUCCESS]
    }

    /** @param {HTMLElement} currentTarget */
    onTabSelected({currentTarget}) {
        if (this.tabsTarget.dataset.initialized !== "true") {
            this.#tryInitTabs()
        } else {
            const id = dsfr(currentTarget)?.tabsGroup?.current?.node?.id
            if (this.tabsTarget.querySelector(`#${id}`) !== null) {
                window.location.hash = `#${id}`
                window.dispatchEvent(new Event("hashchange"))
            }
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

    #tryInitTabs() {
        if (this.tabsTarget.dataset.frJsTabsGroup !== "true") return

        requestAnimationFrame(() => {
            if (window.location.hash !== "") {
                dsfr(this.tabsTarget.querySelector(window.location.hash))?.tabPanel?.disclose()
            }
            this.tabsTarget.dataset.initialized = "true"
        })
    }
}

applicationReady.then(app => app.register("fiche-bloc-commun", FicheBlocCommun))
