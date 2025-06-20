import {choiceJSDefaultOptions} from "/static/core/_custom_choicesjs.js"

export function setUpFreeLinks(element, dataElement){
    const freeLinksChoices = new Choices(element, {
        ...choiceJSDefaultOptions,
        searchResultLimit: 500,
        removeItemButton: true,
        shouldSort: false,
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
