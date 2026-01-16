import {applicationReady} from "Application";
import {Controller} from "Stimulus";


class ArsInformeeController extends Controller {
    static targets = ["origin"]

    onOriginChanged(event){
        if (this.originTarget.value === "ars"){
            document.querySelector('[name="notify_ars"][value="True"]').checked = true
            document.querySelector('[name="modalites_declaration"][value="autre"]').checked = true
        }
    }
}

applicationReady.then(app => {
    app.register("ars-informee", ArsInformeeController)
})
