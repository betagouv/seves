import {applicationReady} from "Application";
import {Controller} from "Stimulus";


class EvenementSimpleController extends Controller {
    static targets = ["notice"]

    onFollowUpChange(event){
        if (event.target.value === "investigation tiac"){
            this.noticeTarget.classList.remove("fr-hidden")
        } else {
            this.noticeTarget.classList.add("fr-hidden")
        }
    }
}

applicationReady.then(app => {
    app.register("evenement-simple-form", EvenementSimpleController)
})
