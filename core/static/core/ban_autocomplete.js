import {choiceJSDefaultOptions} from "/static/core/_custom_choicesjs.js"

/**
 * @typedef {Object} AddressResult
 * @property {string} value
 * @property {string} label
 * @property {Object} customProperties
 * @property {String} customProperties.inseeCode
 * @property {String} customProperties.city
 * @property {String} customProperties.context
 */

/**
 * @param query
 * @param {AbortController=} abortController
 * @returns {Promise<AddressResult[]|undefined>}
 */
export function fetchAddress(query, {abortController = undefined} = {}) {
    const init = {};
    if (abortController !== undefined) {
        init.signal = abortController.signal
    }
    return fetch(`https://api-adresse.data.gouv.fr/search/?q=${query}&limit=15`, init)
        .then(response => response.json())
        .then(data => {
            return data["features"].map(item => (
                {
                    value: item.properties.name,
                    label: item.properties.label,
                    customProperties: {
                        "inseeCode": item.properties.citycode,
                        "city": item.properties.city,
                        "context": item.properties.context
                    }
                }
            ))
        })
        .catch(error => {
            if (error.name === "AbortError") return undefined;
            console.error('Erreur lors de la récupération des données:', error);
            return undefined;
        });
}

export function setUpAddressChoices(element) {
    const addressCommunes = new Choices(element, {
        ...choiceJSDefaultOptions,
        removeItemButton: true,
        placeholderValue: 'Recherchez...',
        shouldSort: false,
    });
    addressCommunes.abortController = new AbortController();
    addressCommunes.abort = () => {
        addressCommunes.abortController.abort();
        addressCommunes.abortController = new AbortController();
    };

    addressCommunes.input.element.addEventListener('input', function (event) {
        const query = addressCommunes.input.element.value
        addressCommunes.clearChoices();
        if (query.length === 0) {
            // Just abort any previous request so we don't fill the dropdown with outdated values
            addressCommunes.abort();
            return addressCommunes;
        }

        const defaultChoices = [
            {
                value: query,
                label: `${query} (Forcer la valeur)`,
                customProperties: {
                    "inseeCode": null,
                    "city": null,
                    "context": null,
                }
            }
        ];

        // Prevent populating dropdown with outdated data and just display default choice
        addressCommunes.abort();
        addressCommunes.setChoices(defaultChoices, 'value', 'label', true);

        if (query.length >= 5) {
            fetchAddress(query, {abortController: addressCommunes.abortController}).then(results => {
                if (Array.isArray(results)) {
                    addressCommunes.setChoices([...defaultChoices, ...results], 'value', 'label', true)
                }
            })
        }
    })
    return addressCommunes
}
