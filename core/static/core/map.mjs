import {applicationReady} from "Application"
import {BaseMapController} from "BaseMapController"
import maplibregl from "MapLibre"

const DISTANT_ZOOM = 5
const CLOSE_UP_ZOOM = 10
const PRECISE_ZOOM = 15

const DEFAULT_CENTER_CONFIG = {center: {lat: 48.866667, lon: 2.333333}, zoom: DISTANT_ZOOM}

const PARCEL_WFS_URL = "https://data.geopf.fr/wfs/ows"
const PARCEL_TYPENAME = "CADASTRALPARCELS.PARCELLAIRE_EXPRESS:parcelle" // "RPG.LATEST:parcelles_graphiques"
const PARCEL_MIN_ZOOM = 12
const PARCEL_THROTTLE_MS = 400
const PARCEL_FILL_OPACITY = 0.15
const PARCEL_OUTLINE_OPACITY = 1
const PARCEL_SOURCE_ID = "parcel-source"
const PARCEL_FILL_LAYER_ID = "parcel-fill"
const PARCEL_OUTLINE_LAYER_ID = "parcel-outline"
const PARCEL_UNAVAILABLE_MESSAGE = "Les parcelles ne sont pas disponibles pour le moment."
const PARCEL_ZOOM_MESSAGE = "Zoomez pour afficher les parcelles."

function throttle(func, wait) {
    let lastCall = 0
    let timeout = null
    return function (...args) {
        const remaining = wait - (Date.now() - lastCall)
        if (remaining <= 0) {
            clearTimeout(timeout)
            timeout = null
            lastCall = Date.now()
            func.apply(this, args)
        } else if (!timeout) {
            timeout = setTimeout(() => {
                lastCall = Date.now()
                timeout = null
                func.apply(this, args)
            }, remaining)
        }
    }
}

class MapController extends BaseMapController {
    static targets = [
        "mapDisplay",
        "latitudeInput",
        "longitudeInput",
        "codeInseeInput",
        "codePostalInput",
        "departementInput",
        "communeSelect",
        "parcellesCheckbox",
        "parcellesMessage",
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
                const feature = json.features?.[0]
                if (!feature) return null
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
        this.addStyleSwitcher(() => {
            if (this.parcellesEnabled) this.refreshParcelles()
        })
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

        if (this.hasParcellesCheckboxTarget) {
            this.parcellesEnabled = false
            const throttledRefresh = throttle(() => this.refreshParcelles(), PARCEL_THROTTLE_MS)
            this.map.on("move", throttledRefresh)
            this.map.on("moveend", () => this.refreshParcelles())
        }
    }

    disconnect() {
        this._parcelAbortController?.abort()
        this.map?.remove()
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

    toggleParcelles() {
        this.parcellesEnabled = this.parcellesCheckboxTarget.checked
        if (this.parcellesEnabled) {
            this.refreshParcelles()
        } else {
            this._parcelAbortController?.abort()
            this.removeParcellesLayer()
            this.clearParcellesMessage()
        }
    }

    refreshParcelles() {
        if (!this.parcellesEnabled) return
        if (this.map.getZoom() < PARCEL_MIN_ZOOM) {
            this.removeParcellesLayer()
            this.showParcellesMessage(PARCEL_ZOOM_MESSAGE)
            return
        }
        this.fetchAndDisplayParcelles()
    }

    fetchAndDisplayParcelles() {
        this._parcelAbortController?.abort()
        const abortController = new AbortController()
        this._parcelAbortController = abortController

        const bounds = this.map.getBounds()
        const bbox = `${bounds.getWest()},${bounds.getSouth()},${bounds.getEast()},${bounds.getNorth()},EPSG:4326`
        const url =
            `${PARCEL_WFS_URL}?SERVICE=WFS&VERSION=2.0.0&REQUEST=GetFeature&TYPENAMES=${PARCEL_TYPENAME}`
            + `&OUTPUTFORMAT=application/json&SRSNAME=EPSG:4326&COUNT=5000&BBOX=${bbox}`

        fetch(url, {signal: abortController.signal})
            .then(res => {
                if (!res.ok) throw new Error(`Unexpected response status: ${res.status}`)
                return res.json()
            })
            .then(geojson => {
                this.clearParcellesMessage()
                this.displayParcellesLayer(geojson)
            })
            .catch(error => {
                if (error.name === "AbortError") return
                console.error("Erreur lors de la récupération des parcelles:", error)
                this.removeParcellesLayer()
                this.showParcellesMessage(PARCEL_UNAVAILABLE_MESSAGE)
            })
    }

    displayParcellesLayer(geojson) {
        const source = this.map.getSource(PARCEL_SOURCE_ID)
        if (source) {
            source.setData(geojson)
            return
        }
        this.map.addSource(PARCEL_SOURCE_ID, {type: "geojson", data: geojson})
        this.map.addLayer({
            id: PARCEL_FILL_LAYER_ID,
            type: "fill",
            source: PARCEL_SOURCE_ID,
            paint: {"fill-color": "#6a4dc4", "fill-opacity": PARCEL_FILL_OPACITY},
        })
        this.map.addLayer({
            id: PARCEL_OUTLINE_LAYER_ID,
            type: "line",
            source: PARCEL_SOURCE_ID,
            paint: {"line-color": "#6a4dc4", "line-width": 2, "line-opacity": PARCEL_OUTLINE_OPACITY},
        })
    }

    removeParcellesLayer() {
        if (this.map.getLayer(PARCEL_OUTLINE_LAYER_ID)) this.map.removeLayer(PARCEL_OUTLINE_LAYER_ID)
        if (this.map.getLayer(PARCEL_FILL_LAYER_ID)) this.map.removeLayer(PARCEL_FILL_LAYER_ID)
        if (this.map.getSource(PARCEL_SOURCE_ID)) this.map.removeSource(PARCEL_SOURCE_ID)
    }

    showParcellesMessage(text) {
        if (!this.hasParcellesMessageTarget) return
        this.parcellesMessageTarget.textContent = text
        this.parcellesMessageTarget.hidden = false
    }

    clearParcellesMessage() {
        if (!this.hasParcellesMessageTarget) return
        this.parcellesMessageTarget.hidden = true
        this.parcellesMessageTarget.textContent = ""
    }
}

applicationReady.then(app => {
    app.register("map", MapController)
})
