import {applicationReady} from "Application";
import {Controller} from "Stimulus";
import choicesDefaults from "choicesDefaults"

class FreeLinksViaApiController  extends Controller {
    static targets = [
        "select",
        "input"
    ]

    debounce(func, wait) {
        let timeout;
        return function (...args) {
            clearTimeout(timeout);
            timeout = setTimeout(() => func.apply(this, args), wait);
        };
    }

    fetchFreeLink(query) {
        return fetch(`/ssa/api/freelinks/recherche/?q=${query}`)
            .then(async response => {
                const data = await response.json();
                return data.results;
            }, error => {
                console.error('Erreur lors de la récupération des données:', error);
                return [];
            })
    }

    syncChoicesToSelect() {
        this.inputTarget.querySelectorAll('option').forEach(o => o.selected = false);

        this.freeLinksChoices.getValue(true).forEach(value => {
            let option = this.inputTarget.querySelector(`option[value="${value}"]`);
            if (!option) {
                option = new Option(value, value, true, true);
                this.inputTarget.add(option);
            }
            option.selected = true;
        });
    }


    connect() {
        this.freeLinksChoices = new Choices(this.selectTarget, {
            ...choicesDefaults,
            searchResultLimit: 500,
            removeItemButton: true,
            placeholderValue: "0000.0000",
            position: 'top',
            noChoicesText: 'Aucune fiche à sélectionner',
            searchFields: ['label'],
        });
        this.freeLinksChoices.input.element.addEventListener('input', this.debounce(() =>{
            const query = this.freeLinksChoices.input.element.value
            if (query.length >= 3) {
                this.fetchFreeLink(query).then(results => {
                    this.freeLinksChoices.setChoices(results, 'value', 'label', false)
                })
            }
        }, 300))

        this.freeLinksChoices.passedElement.element.addEventListener('change', () => {
            this.syncChoicesToSelect();
        });
        this.syncChoicesToSelect();
    }
}

applicationReady.then(app => {
    app.register("free-link-via-api", FreeLinksViaApiController)
})
