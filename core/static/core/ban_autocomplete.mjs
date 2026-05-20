import {applicationReady, COMMON_EVENTS} from "Application"
import choicesDefaults from "choicesDefaults"
import {Controller} from "Stimulus"

/**
 * @typedef {Object} AddressResult
 * @property {string} value
 * @property {string} label
 * @property {Object} customProperties
 * @property {String} customProperties.inseeCode
 * @property {String} customProperties.city
 * @property {String} customProperties.context
 */

/** @param {HTMLElement} element */
export function setUpAddressChoices(element) {
    element.parentElement.dataset.controller = "ban"
    element.dataset.lieuFormTarget = "select"
}

/** @property {HTMLInputElement} selectTarget */
class BanSearchController extends Controller {
    static targets = ["select"]
    static values = {position: {type: String, default: "auto"}}

    /** @type {?Choices} */
    #choiceWidget = null

    /**@type {?AbortController} */
    #abortController = null

    selectTargetConnected(el) {
        this.#choiceWidget = new Choices(el, {
            ...choicesDefaults,
            placeholderValue: "Recherchez…",
            removeItemButton: true,
            position: this.positionValue,
        })
        this.#choiceWidget.input.element.dataset.action = `${this.identifier}#onInput`
    }

    selectTargetDisconnected() {
        this.#choiceWidget?.destroy()
        this.#choiceWidget = null
    }

    setValue(items) {
        this.#choiceWidget?.setValue(Array.isArray(items) ? items : [])
    }

    getUrl(query) {
        return `https://api-adresse.data.gouv.fr/search/?q=${query}&limit=15`
    }

    processResults(value, data) {
        const results = data.features.map(item => ({
            value: item.properties.name,
            label: item.properties.label,
            customProperties: {
                inseeCode: item.properties.citycode,
                postCode: item.properties.postcode,
                city: item.properties.city,
                context: item.properties.context,
                lat: item.geometry.coordinates[1],
                long: item.geometry.coordinates[0],
            },
        }))
        const defaultResult = {
            value: value,
            label: `${value} (Forcer la valeur)`,
            customProperties: {
                inseeCode: null,
                postCode: null,
                city: null,
                context: null,
                lat: null,
                long: null,
            },
        }
        return [defaultResult, ...results]
    }

    async search(query) {
        this.#abortController?.abort()
        this.#abortController = new AbortController()
        try {
            const response = await fetch(this.getUrl(query), {
                signal: this.#abortController?.signal,
            })
            return await response.json()
        } catch (error) {
            if (error.name === "AbortError") return undefined
            console.error(`Erreur lors de la récupération des données: ${error}`)
            return undefined
        }
    }

    /**
     * @param param0
     * @param {string} param0.target.value
     */
    async onInput({target: {value}}) {
        if (value.trim().length >= 2) {
            try {
                const results = await this.search(value)
                if (results !== undefined) {
                    this.#choiceWidget?.clearChoices()
                    this.#choiceWidget?.setChoices(this.processResults(value, results), "value", "label", true)
                }
            } catch (_) {}
        }
    }
}

class CommuneSearchController extends BanSearchController {
    getUrl(query) {
        return `https://geo.api.gouv.fr/communes?nom=${query}&fields=departement,codesPostaux&boost=population&limit=15`
    }

    processResults(_value, data) {
        const result = []
        for (const item of data) {
            for (const postCode of item.codesPostaux) {
                result.push({
                    value: item.nom,
                    label: `${item.nom} (${postCode})`,
                    customProperties: {
                        departementCode: item.departement.code,
                        inseeCode: item.code,
                        postCode,
                    },
                })
            }
        }
        return result
    }
}

applicationReady.then(app => app.register("ban-search", BanSearchController))
applicationReady.then(app => app.register("communes-search", CommuneSearchController))
