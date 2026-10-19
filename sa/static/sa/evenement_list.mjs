import {applicationReady} from "Application"
import {resetForm} from "Forms"
import {Controller} from "Stimulus"

/**
 * @property {HTMLElement} advancedFiltersTarget
 * @property {HTMLButtonElement} advancedFiltersButtonTarget
 * @property {HTMLElement} counterTarget
 */
class EvenementAnimalSearchFormController extends Controller {
    static targets = ["advancedFilters", "advancedFiltersButton", "counter"]

    #savedAdvancedFilters = []

    get advancedFiltersFields() {
        return [...this.advancedFiltersTarget.querySelectorAll("input, select")]
    }

    connect() {
        this.updateCounter()
    }

    onReset() {
        resetForm(this.element)
        this.element.submit()
    }

    openAdvancedFilters() {
        this.#savedAdvancedFilters = this.advancedFiltersFields.map(field => [field, field.value, field.checked])
        this.advancedFiltersTarget.classList.add("open")
        this.advancedFiltersButtonTarget.setAttribute("aria-expanded", "true")
        this.advancedFiltersTarget.querySelector("input, select")?.focus()
    }

    cancelAdvancedFilters() {
        for (const [field, value, checked] of this.#savedAdvancedFilters) {
            field.value = value
            field.checked = checked
        }
        this.closeAdvancedFilters()
    }

    applyAdvancedFilters() {
        if (this.advancedFiltersFields.every(field => field.reportValidity())) {
            this.element.requestSubmit()
        }
    }

    closeAdvancedFilters() {
        this.advancedFiltersTarget.classList.remove("open")
        this.advancedFiltersButtonTarget.setAttribute("aria-expanded", "false")
        this.advancedFiltersButtonTarget.focus()
    }

    updateCounter() {
        const nbFilledFields = this.advancedFiltersFields.filter(field =>
            field.type === "radio" ? field.checked && field.value !== "" : field.value.trim() !== "",
        ).length
        this.counterTarget.textContent = nbFilledFields || ""
        this.counterTarget.classList.toggle("fr-hidden", nbFilledFields === 0)
    }
}

applicationReady.then(app => app.register("evenement-animal-search-form", EvenementAnimalSearchFormController))
