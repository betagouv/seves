import {applicationReady} from "Application"
import {BaseMapController} from "BaseMapController"
import maplibregl from "MapLibre"

class MapViewerController extends BaseMapController {
    static values = {
        lat: Number,
        long: Number,
    }

    connect() {
        const center = [this.longValue, this.latValue]
        this.map = new maplibregl.Map({
            container: this.element,
            center: center,
            zoom: 10,
            attributionControl: false,
            style: "https://openmaptiles.data.gouv.fr/styles/osm-bright/style.json",
        })
        this.addStyleSwitcher()
        this.map.addControl(
            new maplibregl.NavigationControl({
                showZoom: true,
                showCompass: false,
            }),
        )
        new maplibregl.Marker({draggable: false}).setLngLat(center).addTo(this.map)
    }
}

applicationReady.then(app => {
    app.register("map-viewer", MapViewerController)
})
