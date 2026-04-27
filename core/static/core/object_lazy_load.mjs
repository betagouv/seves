import {applicationReady} from "Application"
import {Controller} from "Stimulus"

class ObjectLazyLoad extends Controller {
    static targets = ["objectTag"]

    onPDFPreviewed() {
        const obj = document.createElement("object")
        obj.setAttribute("type", this.objectTagTarget.dataset.type)
        obj.setAttribute("width", this.objectTagTarget.dataset.width)
        obj.setAttribute("height", this.objectTagTarget.dataset.height)
        obj.setAttribute("data", this.objectTagTarget.dataset.src)
        this.objectTagTarget.replaceWith(obj)
    }
}

applicationReady.then(app => app.register("object-lazy-load", ObjectLazyLoad))
