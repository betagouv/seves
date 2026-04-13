import {applicationReady} from "Application"
import {Controller} from "Stimulus"

class ObjectLazyLoad extends Controller {
    static targets = ["objectTag"]

    onPDFPreviewed() {
        this.objectTagTarget.setAttribute("data", this.objectTagTarget.dataset.src)
    }
}

applicationReady.then(app => app.register("object-lazy-load", ObjectLazyLoad))
