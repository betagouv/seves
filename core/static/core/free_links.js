export function setUpFreeLinks(element, dataElement){
    const freeLinksChoices = new Choices(element, {
        searchResultLimit: 500,
        classNames: {
            containerInner: 'fr-select',
        },
        removeItemButton: true,
        shouldSort: false,
        itemSelectText: '',
        noResultsText: 'Aucun résultat trouvé',
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
