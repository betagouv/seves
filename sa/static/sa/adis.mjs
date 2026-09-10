import {applicationReady} from "Application"
import Choices from "Choices"
import choicesDefaults from "choicesDefaults"
import {Controller} from "Stimulus"

class AdisController extends Controller {
    static targets = ["mesures"]
    connect() {
        this.choices = new Choices(this.mesuresTarget, {
            ...choicesDefaults,
            removeItemButton: true,
        })
    }
}

applicationReady.then(app => {
    app.register("adis", AdisController)
})
