import {applicationReady} from "Application"
import choicesDefaults from "choicesDefaults"
import {resetForm} from "Forms"
import {Controller} from "Stimulus"

class SearchFormController extends Controller {
    static targets = ["sidebar", "counter", "dangerSyndromique", "with_free_links", "numero", "annee"]

    onReset() {
        resetForm(this.element)
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
        let filledFields = [...this.sidebarTarget.querySelectorAll("input:not([type='checkbox']), select")]
        filledFields = filledFields.filter(el => el.value.trim() !== "")
        const filledCheckboxes = new Set(
            [...this.sidebarTarget.querySelectorAll("input[type='checkbox']:checked")].map(cb =>
                cb.name.replace("shortcut-", ""),
            ),
        )
        const nbFilledFields = filledFields.length + filledCheckboxes.size
        if (nbFilledFields === 0) {
            this.counterTarget.classList.add("fr-hidden")
        } else {
            this.counterTarget.innerText = nbFilledFields
            this.counterTarget.classList.remove("fr-hidden")
        }
    }

    connect() {
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
