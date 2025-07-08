import choicesDefaults from "choicesDefaults"

export function setUpFreeLinks(element, dataElement){
    const freeLinksChoices = new Choices(element, {
        ...choicesDefaults,
        searchResultLimit: 500,
        removeItemButton: true,
        noChoicesText: 'Aucune fiche à sélectionner',
        searchFields: ['label'],
    });

    if (!!dataElement) {
        const freeLinksIds = JSON.parse(dataElement.textContent);
        if (!!freeLinksIds) {
            freeLinksIds.forEach(value => {
                freeLinksChoices.setChoiceByValue(value);
            });
        }
    }
}
