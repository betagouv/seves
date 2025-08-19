import {AbstractFormSetController} from "BaseFormset"
import {applicationReady} from "Application";


class EtablissementsFormSetController extends AbstractFormSetController {

}

applicationReady.then(app => {
    app.register("etablissement-formset", EtablissementsFormSetController)
})
