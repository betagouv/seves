import {applicationReady} from "Application"
import {resetForm} from "Forms"
import {Controller} from "Stimulus"

class EvenementAnimalSearchFormController extends Controller {
    onReset() {
        resetForm(this.element)
        this.element.submit()
    }
}

applicationReady.then(app => app.register("evenement-animal-search-form", EvenementAnimalSearchFormController))
