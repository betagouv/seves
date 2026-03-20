import {applicationReady} from "Application"
import choicesDefaults from "choicesDefaults"
import {resetForm} from "Forms"
import {Controller} from "Stimulus"

class SearchFormController extends Controller {
    static targets = [
        "form",
        "agent_contact",
        `structure_contact`,
        "sidebar",
        "counter",
        "dangerSyndromique",
        "with_free_links",
        "numero",
        "annee",
    ]

    onReset() {
        resetForm(this.element)
        this.choicesAgentContact.setChoiceByValue("")
        this.choicesStructureContact.setChoiceByValue("")
        this.element.submit()
    }

    onSidebarClear() {
        resetForm(this.sidebarTarget)
        this.dangerSyndromique.removeActiveItems()
    }

    onSidebarAdd() {
        const inputs = this.sidebarTarget.querySelectorAll("input, textarea, select")
        let isValid = true
        inputs.forEach(input => {
            if (!input.checkValidity()) {
                input.reportValidity()
                isValid = false
            }
        })
        if (isValid) {
            this.sidebarTarget.classList.toggle("open")
            document.querySelector(".main-container").classList.toggle("open")
        }
    }

    disableCheckboxIfNeeded() {
        this.with_free_linksTarget.disabled = !(this.numeroTarget.value || this.anneeTarget.value)
    }

    updateFilterCounter() {
        const formData = new FormData(this.formTarget)
        const setValues = new Map()
        for (const [k, v] of formData.entries()) {
            if (v !== "") {
                setValues.set(k, true)
            }
        }

        if (setValues.size === 0) {
            this.counterTarget.classList.add("fr-hidden")
        } else {
            this.counterTarget.innerText = setValues.size
            this.counterTarget.classList.remove("fr-hidden")
        }
    }
    connect() {
        this.choicesAgentContact = new Choices(this.agent_contactTarget, choicesDefaults)
        this.choicesStructureContact = new Choices(this.structure_contactTarget, choicesDefaults)
        this.dangerSyndromique = new Choices(this.dangerSyndromiqueTarget, choicesDefaults)
        this.disableCheckboxIfNeeded()

        this.updateFilterCounter()

        const sidebarClosingObserver = new MutationObserver(mutations => {
            mutations.forEach(mutation => {
                if (mutation.type !== "attributes" && mutation.attributeName !== "class") return
                if (!mutation.target.classList.contains("open")) {
                    this.updateFilterCounter()
                }
            })
        })
        sidebarClosingObserver.observe(this.sidebarTarget, {attributes: true})
    }
}

applicationReady.then(app => {
    app.register("search-form", SearchFormController)
})
