export function fetchAddress(query) {
    return fetch(`https://api-adresse.data.gouv.fr/search/?q=${query}&limit=15`)
        .then(response => response.json())
        .then(data => {
            const results = data["features"].map(item => ({
                value: item.properties.name,
                label: item.properties.label,
                customProperties: {
                    "inseeCode": item.properties.citycode,
                    "city": item.properties.city,
                    "context": item.properties.context
                }
            }))
            return [{
                value: query,
                label: `${query} (Forcer la valeur)`,
                customProperties: {
                    "inseeCode": null,
                    "city": null,
                    "context": null,
                }
            }, ...results];
        })
        .catch(error => {
            console.error('Erreur lors de la récupération des données:', error);
            return []
        });
}

export function setUpAddressChoices(element) {
    const addressCommunes = new Choices(element, {
        removeItemButton: true,
        placeholderValue: 'Recherchez...',
        noResultsText: 'Aucun résultat trouvé',
        noChoicesText: 'Aucun résultat trouvé',
        shouldSort: false,
        searchResultLimit: 10,
        classNames: {containerInner: 'fr-select'},
        itemSelectText: '',
    });
    addressCommunes.input.element.addEventListener('input', function (event) {
        const query = addressCommunes.input.element.value
        if (query.length > 5) {
            fetchAddress(query).then(results => {
                addressCommunes.clearChoices()
                addressCommunes.setChoices(results, 'value', 'label', true)
            })
        }
    })
    return addressCommunes
}
