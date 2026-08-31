import {StyleSwitcherControl} from "MapStyleSwitcher"
import {Controller} from "Stimulus"

export const OSM_STYLE_URL = "https://openmaptiles.data.gouv.fr/styles/osm-bright/style.json"

export class BaseMapController extends Controller {
    static values = {
        jsonFile: String,
        defaultStyle: {type: String, default: "osm"},
    }

    get initialStyleUrl() {
        return this.defaultStyleValue === "satellite" ? this.jsonFileValue : OSM_STYLE_URL
    }

    addStyleSwitcher(onStyleChanged) {
        const styles = [
            {
                id: "osm",
                name: "Carte",
                styleUrl: OSM_STYLE_URL,
                description: "Carte",
            },
            {
                id: "satellite",
                name: "Satellite",
                styleUrl: this.jsonFileValue,
                description: "Satellite",
            },
        ]

        const control = new StyleSwitcherControl({
            styles,
            activeStyleId: this.defaultStyleValue,
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
