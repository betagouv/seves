import {ViewManager, evenementViewModeConfig} from 'ViewManager'
import choicesDefaults from "choicesDefaults"

const viewManager = new ViewManager(evenementViewModeConfig, "evenementViewMode");
viewManager.initialize();

if(!!document.querySelector('#id_transfered_to')){
    new Choices(document.querySelector('#id_transfered_to'), choicesDefaults)
}
