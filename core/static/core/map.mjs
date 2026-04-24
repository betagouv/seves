import {applicationReady} from "Application"
import {BaseMapController} from "BaseMapController"
import maplibregl from "MapLibre"
import {StyleSwitcherControl} from "MapStyleSwitcher"

const DISTANT_ZOOM = 5
const CLOSE_UP_ZOOM = 10
const PRECISE_ZOOM = 15

const DEFAULT_CENTER_CONFIG = {center: {lat: 48.866667, lon: 2.333333}, zoom: DISTANT_ZOOM}
class MapController extends BaseMapController {
    static targets = [
        "mapDisplay",
        "latitudeInput",
        "longitudeInput",
        "communeInput",
        "codeInseeInput",
        "codePostalInput",
        "departementInput",
        "communeSelect",
    ]
    static values = {
        reverseApi: String,
        geoApiRoot: String,
        region: String,
        departement: String,
    }

    async defaultCenterConfig() {
        if (this.regionValue && this.departementValue) {
            console.warn(
                "You set both the value for the region and the departement in the map controller, will default on departement",
            )
        }
        if (this.latitudeInputTarget.value && this.longitudeInputTarget.value) {
            return {
                center: {
                    lat: this.latitudeInputTarget.value,
                    lon: this.longitudeInputTarget.value,
                },
                zoom: PRECISE_ZOOM,
            }
        }

        let url = null

        if (this.regionValue) {
            url = `${this.geoApiRootValue}/regions?nom=${this.regionValue}&limit=1&fields=chefLieu`
        }
        if (this.departementValue) {
            url = `${this.geoApiRootValue}/departements?nom=${this.departementValue}&limit=1&fields=chefLieu`
        }
        if (!url) {
            return DEFAULT_CENTER_CONFIG
        }

        try {
            const chefLieuResponse = await fetch(url)
            const chefLieuJson = await chefLieuResponse.json()
            const chefLieu = chefLieuJson?.[0]?.chefLieu
            const communeResponse = await fetch(`${this.geoApiRootValue}/communes/${chefLieu}?fields=centre`)
            const communeJson = await communeResponse.json()

            return {
                center: {
                    lat: communeJson.centre.coordinates[1],
                    lon: communeJson.centre.coordinates[0],
                },
                zoom: CLOSE_UP_ZOOM,
            }
        } catch (e) {
            console.error(e)
            return DEFAULT_CENTER_CONFIG
        }
    }

    setAddressFieldsByLongLat(e) {
        fetch(`${this.reverseApiValue}?lon=${e.lngLat.lng}&lat=${e.lngLat.lat}&limit=1`)
            .then(res => res.json())
            .then(json => {
                const feature = json.features && json.features[0]
                if (!feature) return null
                this.communeInputTarget.value = feature.properties.city
                this.communeSelectTarget.dispatchEvent(
                    new CustomEvent("forcedChoice", {
                        detail: {
                            value: feature.properties.city,
                        },
                    }),
                )
                this.codeInseeInputTarget.value = feature.properties.citycode
                this.codePostalInputTarget.value = feature.properties.postcode
                const twoDigits = feature.properties.citycode.slice(0, 2)
                const threeDigits = feature.properties.citycode.slice(0, 3)
                const options = Array.from(this.departementInputTarget.options)
                const match = options.find(o => o.value === twoDigits) || options.find(o => o.value === threeDigits)

                if (!match) return

                this.departementInputTarget.value = match.value
            })
            .catch(error => {
                console.error("Erreur lors de la récupération des données:", error)
                return undefined
            })
    }

    handleDoubleClickOnMap(e) {
        this.marker.setLngLat(e.lngLat)
        this.latitudeInputTarget.value = e.lngLat.lat
        this.longitudeInputTarget.value = e.lngLat.lng
        this.setAddressFieldsByLongLat(e)
    }

    async connect() {
        const {center, zoom} = await this.defaultCenterConfig()
        this.map = new maplibregl.Map({
            container: this.mapDisplayTarget,
            center: center,
            zoom: zoom,
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

        this.marker = new maplibregl.Marker({draggable: false}).setLngLat(center).addTo(this.map)
        this.map.on("dblclick", e => {
            this.handleDoubleClickOnMap(e)
        })
    }

    onCoordinateChange() {
        const lat = parseFloat(this.latitudeInputTarget.value)
        const lon = parseFloat(this.longitudeInputTarget.value)
        if (Number.isNaN(lat) || Number.isNaN(lon)) {
            return
        }
        this.marker.setLngLat({lat, lon})
        this.map.setCenter({lat, lon})
        this.map.setZoom(PRECISE_ZOOM)
    }
}

applicationReady.then(app => {
    app.register("map", MapController)
})
