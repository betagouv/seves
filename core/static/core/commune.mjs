import choicesDefaults from "choicesDefaults"

export function fetchCommunes(query) {
    return fetch(
        `https://geo.api.gouv.fr/communes?nom=${query}&fields=departement,codesPostaux&boost=population&limit=15`,
    )
        .then(response => response.json())
        .then(data => {
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
        })
        .catch(error => {
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
    choicesCommunes.input.element.addEventListener("input", () => {
        const query = choicesCommunes.input.element.value
        if (query.length > 2) {
            fetchCommunes(query).then(results => {
                choicesCommunes.clearChoices()
                choicesCommunes.setChoices(results, "value", "label", true)
            })
        }
    })
    return choicesCommunes
}
