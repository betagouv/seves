import {applicationReady} from "Application"
import {Controller} from "Stimulus"

/**
 * @property {HTMLInputElement} categorieDangerInputTarget
 * @property {HTMLElement[]} pamContainerTargets
 * @property {HTMLElement} noticeTarget
 * @property {HTMLElement} noticeTextTarget
 */
class TreeselectCategorieMessages extends Controller {
    static targets = ["categorieDangerInput", "pamContainer", "notice", "noticeText"]
    static values = {danger: Object}

    #dangersBacteriens = new Set()

    initialize() {
        this.#dangersBacteriens = new Set(
            JSON.parse(this.element.querySelector("#dangers-bacteriens")?.innerText ?? "[]"),
        )
    }

    /** @param {HTMLInputElement} el */
    async categorieDangerInputTargetConnected(el) {
        if (el.type === "radio" && el.checked) {
            el.dispatchEvent(new Event("change"))
        }
    }

    onCategorieDangerSelected({target}) {
        const show = target.checked && this.#dangersBacteriens.has(target.value)
        for (const it of this.pamContainerTargets) {
            it.classList.toggle("fr-hidden", !show)
        }

        if (target.dataset.group ?? false) {
            const value = target.labels?.[0]?.textContent?.trim() ?? target.ariaLabel ?? target.value
            this.noticeTextTarget.innerText = `Il existe des sous-catégories pour « ${value} » : pensez à préciser dès que possible.`
            this.noticeTarget.classList.remove("fr-hidden")
        } else {
            this.noticeTarget.classList.add("fr-hidden")
        }
    }
}

applicationReady.then(app => app.register("treeselect-categorie-messages", TreeselectCategorieMessages))
