import {Controller} from "Stimulus";
import {useStore} from "StimulusStore"

export class AbstractFormSetController extends Controller {
    static MGMT_FORM_FIELDS = {
        TOTAL_FORMS: Number,
        INITIAL_FORMS: Number,
        MIN_NUM_FORMS: Number,
        MAX_NUM_FORMS: Number,
    }

    static targets = ["emptyFormTpl", "formsetContainer", ...Object.keys(this.MGMT_FORM_FIELDS)]
    static values = { ...this.MGMT_FORM_FIELDS }

    connect() {
        if (this.constructor.stores) {
            useStore(this)
        }
        this._initializeFieldValues()
    }

    _initializeFieldValues() {
        for (const fieldName of Object.keys(this.constructor.MGMT_FORM_FIELDS)) {
            if (!this[`has${fieldName}Target`]) {
                const htmlAttr = this.context.scope.schema.targetAttributeForScope(this.identifier)
                console.debug(`Missing target with HTML attribute "${htmlAttr}=${fieldName}"`)
                continue
            }
            this[`${fieldName}Value`] = this[`${fieldName}Target`].value
            this[`${fieldName}ValueChanged`] = value => {
                this[`${fieldName}Target`].value = value
            }
        }
    }

    onAddForm() {
        const html = this.emptyFormTplTarget.innerHTML.replace(/__prefix__/g, `${this.TOTAL_FORMSValue}`)
        this.formsetContainerTarget.insertAdjacentHTML("beforeend", html)
        this.TOTAL_FORMSValue += 1
    }
}
