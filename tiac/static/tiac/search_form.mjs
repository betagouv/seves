import {Controller} from "Stimulus";
import {applicationReady} from "Application";
import {resetForm} from "Forms"
import choicesDefaults from "choicesDefaults"


class SearchFormController extends Controller {
  static targets = ["agent_contact", "structure_contact"]

  onReset(){
    resetForm(this.element)
    this.choicesAgentContact.setChoiceByValue('');
    this.choicesStructureContact.setChoiceByValue('');
    this.element.submit()
  }

  connect(){
    this.choicesAgentContact = new Choices(this.agent_contactTarget, choicesDefaults);
    this.choicesStructureContact = new Choices(this.structure_contactTarget, choicesDefaults);
  }
}

applicationReady.then(app => {
  app.register("search-form", SearchFormController)
})
