import choicesDefaults from "choicesDefaults"

export function fetchCommunes(query) {
    return fetch(`https://geo.api.gouv.fr/communes?nom=${query}&fields=departement&boost=population&limit=15`)
        .then((response) => response.json())
        .then((data) => {
            return data.map((item) => ({
                value: item.nom,
                label: `${item.nom} (${item.departement.code})`,
                customProperties: {
                    departementCode: item.departement.code,
                    inseeCode: item.code,
                },
            }))
        })
        .catch((error) => {
            console.error("Erreur lors de la récupération des données:", error)
            return []
        })
}

export function setUpCommuneChoices(element) {
    const choicesCommunes = new Choices(element, {
        ...choicesDefaults,
        removeItemButton: true,
        placeholderValue: "Recherchez…",
    })
    choicesCommunes.input.element.addEventListener("input", function (event) {
        const query = choicesCommunes.input.element.value
        if (query.length > 2) {
            fetchCommunes(query).then((results) => {
                choicesCommunes.clearChoices()
                choicesCommunes.setChoices(results, "value", "label", true)
            })
        }
    })
    return choicesCommunes
}
