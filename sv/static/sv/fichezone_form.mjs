import {Controller} from "Stimulus";
import {useStore, createStore} from "StimulusStore"
import {applicationReady} from "Application"
import Choices from "Choices"
import choicesDefaults from "choicesDefaults"


const choicesStore = createStore({
    name: "selectedChoices",
    type: Array,
    initialValue: [],
});


/**
 * @property {HTMLSelectElement} formDetectionsSelectTarget
 * @property {import("StimulusStore/dist/types/updateMethod").UpdateMethod} setSelectedChoicesValue
 */
class ZoneInfesteeController extends Controller {
    static stores = [choicesStore]
    static targets = ["formDetectionsSelect"]

    initialize() {
        /** @type {Choices|undefined} */
        this.choices = undefined
    }

    connect() {
        useStore(this)

        this.choices = new Choices(this.formDetectionsSelectTarget, {
            ...choicesDefaults,
            searchResultLimit: 500,
            removeItemButton: true,
            noChoicesText: "Aucune fiche détection à sélectionner",
            searchFields: ["label"],
        })
        this.addChoices(...this.choices.getValue(true))
    }

    onChoice({detail: {value}}) {
        this.addChoices(value)
    }

    onRemoveItem({detail: {value}}) {
        this.removeChoices(value)
    }

    addChoices(...values) {
        this.setSelectedChoicesValue(previousValue => [...previousValue, ...values])
    }

    removeChoices(...values) {
        this.setSelectedChoicesValue(previousValue => previousValue.filter(value => !values.includes(value)))
    }

    /** @param {String[]} value */
    onSelectedChoicesUpdate(value) {
        if (this.choices === undefined) return;

        this.choices.enable()
        const currentChoices = this.choices.passedElement.optionsAsChoices()
        const updatedChoices = currentChoices.map(choice => ({
            value: choice.value,
            label: choice.label,
            /* We don't want to disable this option if it is selected */
            disabled: value.includes(choice.value) && !choice.selected,
            selected: choice.selected
        }));
        this.choices.clearChoices()
        this.choices.setChoices(updatedChoices, "value", "label", false);
    }
}

class DetectionsHorsZoneController extends ZoneInfesteeController {}

/**
 * @property {HTMLInputElement} deleteInputTarget
 */
class ZoneInfesteeFormController extends ZoneInfesteeController {
    static targets = [...ZoneInfesteeController.targets, "deleteInput"]
    static stores = ZoneInfesteeController.stores

    onDelete() {
        this.deleteInputTarget.value = "on"
        this.element.setAttribute("hidden", "hidden")
        this.element.setAttribute("aria-hidden", "true")

        if (this.choices !== undefined) {
            this.removeChoices(this.choices.getValue(true))
        }
    }
}


const MGMT_FORM_FIELDS = {
    TOTAL_FORMS: Number,
    INITIAL_FORMS: Number,
    MIN_NUM_FORMS: Number,
    MAX_NUM_FORMS: Number,
}


/**
 * @property {Number} TOTAL_FORMSValue
 * @property {HTMLTemplateElement} emptyFormTplTarget
 * @property {HTMLElement} formsetContainerTarget
 * @property {String[]} selectedChoicesValue
 */
class ZoneInfesteeFormSetController extends Controller {
    static targets = [...Object.keys(MGMT_FORM_FIELDS), "emptyFormTpl", "formsetContainer", "formDetectionsSelect"]
    static values = {...MGMT_FORM_FIELDS, selectedChoices: Array}
    static stores = [choicesStore]

    connect() {
        useStore(this)
        for (const fieldName of Object.keys(MGMT_FORM_FIELDS)) {
            if (!this[`has${fieldName}Target`]) {
                const htmlAttr = this.context.scope.schema.targetAttributeForScope(this.identifier)
                console.debug(`Missing target with HTML attribute "${htmlAttr}="${fieldName}"`)
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


applicationReady.then(app => {
    app.register("zone-infestee-form", ZoneInfesteeFormController)
    app.register("hors-zone", DetectionsHorsZoneController)
    app.register("zone-infestee-formset", ZoneInfesteeFormSetController)
})
