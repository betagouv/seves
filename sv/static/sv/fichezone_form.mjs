import { Controller } from "Stimulus"
import { useStore, createStore } from "StimulusStore"
import { applicationReady } from "Application"
import Choices from "Choices"
import choicesDefaults from "choicesDefaults"
import { BaseFormSetController } from "BaseFormset"

const choicesStore = createStore({
    name: "selectedChoices",
    type: Array,
    initialValue: [],
})

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

    onChoice({ detail: { value } }) {
        this.addChoices(value)
    }

    onRemoveItem({ detail: { value } }) {
        this.removeChoices(value)
    }

    addChoices(...values) {
        this.setSelectedChoicesValue((previousValue) => [...previousValue, ...values])
    }

    removeChoices(...values) {
        this.setSelectedChoicesValue((previousValue) => previousValue.filter((value) => !values.includes(value)))
    }

    /** @param {String[]} value */
    onSelectedChoicesUpdate(value) {
        if (this.choices === undefined) return

        this.choices.enable()
        const currentChoices = this.choices.passedElement.optionsAsChoices()
        const updatedChoices = currentChoices.map((choice) => ({
            value: choice.value,
            label: choice.label,
            /* We don't want to disable this option if it is selected */
            disabled: value.includes(choice.value) && !choice.selected,
            selected: choice.selected,
        }))
        this.choices.clearChoices()
        this.choices.setChoices(updatedChoices, "value", "label", false)
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

class ZoneInfesteeFormSetController extends BaseFormSetController {
    static targets = [...BaseFormSetController.targets, "formDetectionsSelect"]
    static values = { ...BaseFormSetController.values, selectedChoices: Array }
    static stores = [choicesStore]

    connect() {
        useStore(this)
        this._initializeFieldValues()
    }
}

applicationReady.then((app) => {
    app.register("zone-infestee-form", ZoneInfesteeFormController)
    app.register("hors-zone", DetectionsHorsZoneController)
    app.register("zone-infestee-formset", ZoneInfesteeFormSetController)
})
