import {applicationReady} from "Application"
import choicesDefaults from "choicesDefaults"
import {Controller} from "Stimulus"

/** @property {HTMLSelectElement} selectTarget */
class EspeceSearch extends Controller {
    static targets = ["select"]

    /** @type {?Choices} */
    #choiceWidget = null

    selectTargetConnected(el) {
        this.#choiceWidget = new Choices(el, {
            ...choicesDefaults,
            removeItemButton: true,
            placeholderValue: "Tapez minimum 2 caractères",
            searchResultLimit: 50,
            position: "bottom",
        })
        this.#choiceWidget.input.element.dataset.action = `${this.identifier}#onInput`
    }

    selectTargetDisconnected() {
        this.#choiceWidget?.destroy()
        this.#choiceWidget = null
    }

    async search(query) {
        try {
            const response = await fetch(`/sv/api/espece/recherche/?q=${query}`)
            const data = await response.json()
            return data.results.map(item => ({
                value: item.id,
                label: item.name,
            }))
        } catch (error) {
            console.error("Erreur lors de la récupération des données:", error)
            return []
        }
    }

    /**
     * @param param0
     * @param {string} param0.target.value
     */
    async onInput({target: {value}}) {
        if (value.trim().length >= 2) {
            this.#choiceWidget?.clearChoices()
            this.#choiceWidget?.setChoices(await this.search(value), "value", "label", true)
        }
    }
}

applicationReady.then(app => app.register("espece-search", EspeceSearch))
