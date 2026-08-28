import {applicationReady} from "Application"
import {Controller} from "Stimulus"

const EMBED_SCRIPT_ID = "metabase-embed-script"

class MetabaseController extends Controller {
    static values = {url: String}

    connect() {
        window.metabaseConfig = {
            theme: {preset: "light"},
            isGuest: true,
            instanceUrl: this.urlValue,
        }

        if (!document.getElementById(EMBED_SCRIPT_ID)) {
            const script = document.createElement("script")
            script.id = EMBED_SCRIPT_ID
            script.src = `${this.urlValue}/app/embed.js`
            script.defer = true
            document.head.appendChild(script)
        }
    }
}

applicationReady.then(app => {
    app.register("metabase", MetabaseController)
})
