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
    static values = ["currentOption", "selectedValues", "config"]

    connect() {
        this.selectedValues = []
        this.config = JSON.parse(this.jsonConfigTarget.textContent)
    }

    onShowFirstModal() {
        dsfr(this.etiologieModalTarget).modal.disclose();
        document.querySelectorAll('input[name="danger_syndromiques_suspectes_display"]').forEach(el => {
            el.disabled = this.selectedValues.includes(el.value)
        })
    }

    onDelete(event){
        this.selectedValues.pop(event.target.dataset.value)
        this.renderCards()
    }

    renderCard(choice) {
        const item = this.config.find(d => d.value === choice);
        return `
         <div class="etiologie-card-container fr-p-4w fr-mb-4w">
                <div class="fr-grid-row fr-grid-row--gutters fr-col">
                    <div class="fr-col-12 fr-col-lg-4">${item.name}</div>
                    <div class="fr-col-12 fr-col-lg-4">${item.help_text}</div>
                    <div class="fr-col-12 fr-col-lg-3">Recommendations</div>
                    <div class="fr-col-12 fr-col-lg-1">
                    <button
                                            class="fr-btn fr-icon-delete-line fr-btn--secondary fr-btn--sm"
                                            data-value="${choice}"
                                            data-action="${this.identifier}#onDelete:prevent:default"
                                        >Supprimer</button>
</div>
                </div></div>`
    }

    renderCards(){
        this.etiologieCardContainerTarget.innerHTML =""
        if (this.selectedValues.length > 0){
            this.selectedValues.forEach(it =>this.etiologieCardContainerTarget.insertAdjacentHTML("beforeend", this.renderCard(it)))
            this.etiologieEmptyCardContainerTarget.classList.add("fr-hidden")
        } else {
            this.etiologieEmptyCardContainerTarget.classList.remove("fr-hidden")
        }
        this.hiddenFieldTarget.value = JSON.stringify(this.selectedValues)
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
        this.selectedValues.push(this.currentOption)
        this.currentOption = null
        this.renderCards()
    }
}

applicationReady.then(app => {
    app.register("etiologie-form", EtiologieFormController)
})
