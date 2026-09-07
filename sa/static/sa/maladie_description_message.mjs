import {applicationReady} from "Application"
import {Controller} from "Stimulus"

class MaladieDescriptionMessage extends Controller {
    static targets = ["maladieInput", "notice", "noticeText"]

    #descriptions = {}

    initialize() {
        this.#descriptions = JSON.parse(this.element.querySelector("#maladie-descriptions")?.innerText ?? "{}")
    }

    maladieInputTargetConnected(el) {
        if (el.type === "radio" && el.checked) {
            el.dispatchEvent(new Event("change"))
        }
    }

    onMaladieSelected({target}) {
        const description = target.checked ? this.#descriptions[target.value] : undefined
        if (description) {
            this.noticeTextTarget.innerText = description
            this.noticeTarget.classList.remove("fr-hidden")
        } else {
            this.noticeTarget.classList.add("fr-hidden")
        }
    }
}

applicationReady.then(app => app.register("maladie-description-message", MaladieDescriptionMessage))
