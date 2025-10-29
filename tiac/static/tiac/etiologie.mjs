import {applicationReady} from "Application";
import {Controller} from "Stimulus";


class EtiologieFormController  extends Controller {
    static targets = [
        "etiologieModal",
        "etiologieModalConfirmation",
        "etiologieModalConfirmationContent",
        "etiologieEmptyCardContainer",
        "etiologieCardContainer",
        "hiddenField",
        "jsonConfig"
    ]
    static values = {currentOption:String, selectedValues: Array, config: Object, hasConnected: {type: Boolean, default: false}};

    connect() {
        this.config = JSON.parse(this.jsonConfigTarget.textContent)
        this.selectedValuesValue = this.hiddenFieldTarget.value.split("||").filter(value => value.length > 0)
        this.hasConnectedValue = true
    }

    onShowFirstModal() {
        dsfr(this.etiologieModalTarget).modal.disclose();
        document.querySelectorAll('input[name="danger_syndromiques_suspectes_display"]').forEach(el => {
            el.disabled = this.selectedValuesValue.includes(el.value)
        })
    }

    onDelete({params:{choice}}){
        this.selectedValuesValue = this.selectedValuesValue.filter(it => it !== choice)
    }

    renderRecommendation = (choice, description) => {
        if (!description) return '<div class="fr-col-12 fr-col-lg-3"></div>';
        return `
        <div class="fr-col-12 fr-col-lg-3">Recommandations
            <button aria-describedby="tooltip-${choice}" type="button" class="fr-btn--tooltip fr-btn">infobulle</button>
            <span class="fr-tooltip fr-placement" id="tooltip-${choice}" role="tooltip">${description}</span>
        </div>`;
    }


    renderCard(choice) {
        const item = this.config.find(d => d.value === choice);
        return `<div class="etiologie-card-container fr-p-4w fr-mb-2w">
            <div class="fr-grid-row fr-grid-row--gutters fr-col">
                <div class="fr-col-12 fr-col-lg-4">${item.name}</div>
                <div class="fr-col-12 fr-col-lg-4">${item.help_text}</div>
                ${this.renderRecommendation(choice, item.description)}
                <div class="fr-col-12 fr-col-lg-1">
                    <button
                        class="fr-btn fr-icon-delete-line fr-btn--secondary fr-btn--sm"
                        data-${this.identifier}-choice-param="${choice}"
                        data-action="${this.identifier}#onDelete:prevent:default">
                        Supprimer
                    </button>
                </div>
            </div>
        </div>`
    }

    renderCards(){
        this.etiologieCardContainerTarget.innerHTML =""
        if (this.selectedValuesValue.length > 0){
            this.selectedValuesValue.forEach(it =>this.etiologieCardContainerTarget.insertAdjacentHTML("beforeend", this.renderCard(it)))
            this.etiologieEmptyCardContainerTarget.classList.add("fr-hidden")
        } else {
            this.etiologieEmptyCardContainerTarget.classList.remove("fr-hidden")
        }
    }

    /** @param {string[]} newValue */
    selectedValuesValueChanged(newValue) {
        if(!this.hasConnectedValue) return;
        this.renderCards()
        this.hiddenFieldTarget.value = newValue.join("||")
    }

    onChooseOption(){
        const checked = document.querySelector('input[name="danger_syndromiques_suspectes_display"]:checked');
        if (!checked){return;}
        this.currentOption = checked.value
        this.etiologieModalConfirmationContentTarget.innerHTML = document.querySelector("#" + this.currentOption.replaceAll(" ", "-")).innerHTML
        dsfr(this.etiologieModalConfirmationTarget).modal.disclose();
    }

    onConfirm(){
        dsfr(this.etiologieModalConfirmationTarget).modal.conceal();
        this.selectedValuesValue = [...this.selectedValuesValue, this.currentOption]
        this.currentOption = null
    }
}

applicationReady.then(app => {
    app.register("etiologie-form", EtiologieFormController)
})
