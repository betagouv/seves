function debounce(func, wait) {
    let timeout;
    return function (...args) {
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(this, args), wait);
    };
}

export function fetchSiret(value, token) {
    const url = 'https://api.insee.fr/entreprises/sirene/siret?q=siren%3A' + value.replaceAll(" ", "")+ '* AND -periode(etatAdministratifEtablissement:F)';
    const headers = {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
    };
    let results = []
    return fetch(url, {method: 'GET', headers: headers})
        .then(response => response.json())
        .then(data => {
            if (!data["etablissements"]){
                return []
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
            return results
        });
}

export function setUpSiretChoices(element, position){
    const choicesSIRET = new Choices(element, {
        removeItemButton: true,
        placeholderValue: 'N° SIRET',
        noResultsText: 'Aucun résultat trouvé',
        noChoicesText: 'Aucun résultat trouvé',
        shouldSort: false,
        searchResultLimit: 20,
        classNames: {containerInner: 'fr-select'},
        itemSelectText: '',
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
