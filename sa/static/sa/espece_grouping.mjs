import {applicationReady} from "Application"
import {Controller} from "Stimulus"
import {normalize} from "Utils"

const FREQUENT_GROUP_LABEL = "Les plus fréquentes"
const OTHER_GROUP_LABEL = "Autres"

class EspeceGrouping extends Controller {
    static targets = ["maladieInput", "especeWidget"]

    #byMaladie = {}
    #defaultIds = []

    initialize() {
        this.#byMaladie = JSON.parse(this.element.querySelector("#especes-concernees-by-maladie")?.innerText ?? "{}")
        this.#defaultIds = JSON.parse(this.element.querySelector("#especes-courantes-ids")?.innerText ?? "[]")
    }

    maladieInputTargetConnected(el) {
        if (el.type === "radio" && el.checked) {
            el.dispatchEvent(new Event("change"))
        }
    }

    onMaladieSelected({target}) {
        if (!target.checked) return
        const frequentIds = new Set((this.#byMaladie[target.value] ?? this.#defaultIds).map(String))
        this.#regroup(frequentIds)
    }

    #regroup(frequentIds) {
        const groups = this.#groupContainers()
        if (!groups) return

        const elements = [...this.especeWidgetTarget.querySelectorAll(".fr-treeselect__element")]
        const withLabel = elements.map(el => {
            const input = el.querySelector("input")
            return {
                el,
                id: input.value.trim(),
                sortLabel: normalize(input.labels[0]?.textContent.trim() ?? ""),
            }
        })
        withLabel.sort((a, b) => a.sortLabel.localeCompare(b.sortLabel))

        for (const {el, id} of withLabel) {
            const target = frequentIds.has(id) ? groups.frequent : groups.other
            target.appendChild(el)
        }
    }

    #groupContainers() {
        const headers = [...this.especeWidgetTarget.querySelectorAll(".fr-treeselect__group-header")]
        const containerFor = label => {
            const header = headers.find(it => it.textContent.trim() === label)
            return header?.closest(".fr-treeselect__group")?.querySelector('[data-testid="group-container"]')
        }
        const frequent = containerFor(FREQUENT_GROUP_LABEL)
        const other = containerFor(OTHER_GROUP_LABEL)
        if (!frequent || !other) return null
        return {frequent, other}
    }
}

applicationReady.then(app => app.register("espece-grouping", EspeceGrouping))
