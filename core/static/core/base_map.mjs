import {StyleSwitcherControl} from "MapStyleSwitcher"
import {Controller} from "Stimulus"

export class BaseMapController extends Controller {
    static values = {
        jsonFile: String,
    }

    addStyleSwitcher(onStyleChanged) {
        const styles = [
            {
                id: "osm",
                name: "Carte",
                styleUrl: "https://openmaptiles.data.gouv.fr/styles/osm-bright/style.json",
                description: "Carte",
            },
            {
                id: "satellite",
                name: "Vue Satellite",
                styleUrl: this.jsonFileValue,
                description: "Vue Satellite",
            },
        ]

        const control = new StyleSwitcherControl({
            styles,
            activeStyleId: "osm",
            theme: "auto",
            showImages: false,
            onAfterStyleChange: (_from, to) => {
                this.map.setStyle(to.styleUrl)
                if (onStyleChanged) this.map.once("idle", onStyleChanged)
            },
        })
        this.map.addControl(control, "bottom-left")
    }
}
