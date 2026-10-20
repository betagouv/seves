import {applicationReady} from "Application"
import {Controller} from "Stimulus"

/**
 * ******** Values ********
 * @property {String} sourceDoListerioseValue
 * @property {String} dangerDoListerioseValue
 * @property {String} dangerInputNameValue
 */
class InvestigationCasHumainFormController extends Controller {
    static values = {sourceDoListeriose: String, dangerDoListeriose: String, dangerInputName: String}

    #hasPreselectedDanger = false

    /** @return {HTMLInputElement} */
    get dangerDoListerioseInput() {
        return this.element.form.querySelector(
            `input[name="${this.dangerInputNameValue}"][value="${this.dangerDoListerioseValue}"]`,
        )
    }

    onSourceChange({target: {value}}) {
        const input = this.dangerDoListerioseInput
        if (value === this.sourceDoListerioseValue) {
            if (!input.checked) {
                this.#setChecked(input, true)
                this.#hasPreselectedDanger = true
            }
        } else if (this.#hasPreselectedDanger) {
            this.#hasPreselectedDanger = false
            if (input.checked) {
                this.#setChecked(input, false)
            }
        }
    }

    /**
     * @param {HTMLInputElement} input
     * @param {boolean} checked
     */
    #setChecked(input, checked) {
        input.checked = checked
        input.dispatchEvent(new Event("change"))
    }
}

applicationReady.then(app => app.register("investigation-cas-humain-form", InvestigationCasHumainFormController))
