import { Controller } from "Stimulus"
import { useStore } from "StimulusStore"

/**
 * @property {boolean} hasEmptyFormTplTarget
 * @property {boolean} hasFormsetContainerTarget
 * @property {HTMLTemplateElement} emptyFormTplTarget
 * @property {HTMLElement} formsetContainerTarget
 */
export class BaseFormSetController extends Controller {
    static MGMT_FORM_FIELDS = {
        TOTAL_FORMS: Number,
        INITIAL_FORMS: Number,
        MIN_NUM_FORMS: Number,
        MAX_NUM_FORMS: Number,
    }

    static targets = ["emptyFormTpl", "formsetContainer", ...Object.keys(this.MGMT_FORM_FIELDS)]
    static values = { ...this.MGMT_FORM_FIELDS }

    connect() {
        this._initializeFieldValues()
    }

    _initializeFieldValues() {
        const htmlAttr = this.context.scope.schema.targetAttributeForScope(this.identifier)
        for (const fieldName of Object.keys(this.constructor.MGMT_FORM_FIELDS)) {
            if (!this[`has${fieldName}Target`]) {
                console.debug(
                    `Missing target with HTML attribute ${htmlAttr}="${fieldName}". Did you render the management form with the correct data attributes?`,
                )
                continue
            }
            this[`${fieldName}Value`] = this[`${fieldName}Target`].value
            this[`${fieldName}ValueChanged`] = (value) => {
                this[`${fieldName}Target`].value = value
            }
        }
        if (!this.hasEmptyFormTplTarget) {
            console.debug(
                `Missing target with HTML attribute ${htmlAttr}="emptyFormTpl". This template will be used to create new forms.`,
            )
        }
        if (!this.hasFormsetContainerTarget) {
            console.debug(
                `Missing target with HTML attribute ${htmlAttr}="formsetContainer". This is where new forms will be added.`,
            )
        }
    }

    onAddForm() {
        const html = this.emptyFormTplTarget.innerHTML.replace(/__prefix__/g, `${this.TOTAL_FORMSValue}`)
        this.formsetContainerTarget.insertAdjacentHTML("beforeend", html)
        this.TOTAL_FORMSValue += 1
        return this.formsetContainerTarget.lastElementChild
    }
}
