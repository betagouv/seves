import choicesDefaults from "choicesDefaults"
import Choices from "Choices";

function debounce(func, wait) {
    let timeout;
    return function (...args) {
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(this, args), wait);
    };
}

function improveResults(value, results) {
    const filteredResults = results.filter(item =>
        item.customProperties?.siret?.startsWith(value)
    )

    if (value.length === 14) {
        return [{
            value: value,
            label: `${value} (Forcer la valeur)`,
            customProperties: {
                "streetData": null,
                "fullStreetData": null,
                "siret": value,
                "raison": null,
                "commune": null,
                "code_commune": null,
            }
        }, ...filteredResults]
    }
    return filteredResults
}

export function fetchSiret(value, token) {
    const cleanedValue =  value.replaceAll(" ", "")
    const siren =  cleanedValue.substring(0, 9);
    const url = `https://api.insee.fr/entreprises/sirene/siret?nombre=100&q=siren%3A${siren}* AND -periode(etatAdministratifEtablissement:F)`;
    const headers = {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
    };
    let results = []
    return fetch(url, {method: 'GET', headers: headers})
        .then(response => response.json())
        .then(data => {
            if (!data["etablissements"]){
                return improveResults(cleanedValue, [])
            }
            data["etablissements"].forEach((etablissement) => {
                let address = etablissement["adresseEtablissement"]
                let streetData = `${address["numeroVoieEtablissement"]} ${address["typeVoieEtablissement"]} ${address["libelleVoieEtablissement"]}`
                let fullStreetData = `${streetData} - ${address["codePostalEtablissement"]} ${address["libelleCommuneEtablissement"]}`
                let resultEtablissement = `${etablissement["siret"]} - ${fullStreetData}`
                const uniteLegale = etablissement["uniteLegale"]
                let resultUnite = `${uniteLegale["denominationUniteLegale"]?? ""} ${uniteLegale["denominationUniteLegale"]?? ""} ${uniteLegale["prenom1UniteLegale"]?? ""} ${uniteLegale["nomUniteLegale"]?? ""}`
                results.push({
                    value: etablissement["siret"],
                    label: resultUnite + " " + resultEtablissement ,
                    customProperties: {
                        "streetData": streetData,
                        "fullStreetData": fullStreetData,
                        "siret": etablissement["siret"],
                        "raison": uniteLegale["denominationUniteLegale"],
                        "commune": address["libelleCommuneEtablissement"],
                        "code_commune": address["codeCommuneEtablissement"],
                    }
                })
            });
            return improveResults(cleanedValue, results)
        });
}

/**
 *
 * @param {HTMLInputElement} element Element to bin Choices to
 * @param {"auto"|"top"|"bottom"} position The position of the dropdown
 * @returns {Choices}
 */
export function setUpSiretChoices(element, position){
    const choicesSIRET = new Choices(element, {
        ...choicesDefaults,
        removeItemButton: true,
        placeholderValue: 'N° SIRET',
        searchResultLimit: 20,
        position: position,
    });

    choicesSIRET.input.element.addEventListener('input', debounce((event) => {
        const query = choicesSIRET.input.element.value
        if (query.length > 5) {
            fetchSiret(query, element.dataset.token).then(results => {
                choicesSIRET.clearChoices()
                choicesSIRET.setChoices(results, 'value', 'label', true)
            })
        }
    }, 300))
    return choicesSIRET
}
