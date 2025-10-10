import {Controller} from "Stimulus";
import {applicationReady} from "Application";
import {resetForm} from "Forms"
import choicesDefaults from "choicesDefaults"


class SearchFormController extends Controller {
  static targets = ["agent_contact", "structure_contact", "sidebar", "counter"]

  onReset(){
    resetForm(this.element)
    this.choicesAgentContact.setChoiceByValue('');
    this.choicesStructureContact.setChoiceByValue('');
    this.element.submit()
  }

  onSidebarClear(){
    resetForm(this.sidebarTarget)
  }

  onSidebarAdd() {
    this.sidebarTarget.classList.toggle('open');
    document.querySelector('.main-container').classList.toggle('open')
  }

  updateFilterCounter(){
    let filledFields = [...this.sidebarTarget.querySelectorAll('input, select')]
    filledFields = filledFields.filter(el => el.value.trim() !== '');

    if (filledFields.length === 0){
      this.counterTarget.classList.add("fr-hidden")
    } else {
      this.counterTarget.innerText = filledFields.length
      this.counterTarget.classList.remove("fr-hidden")
    }
  }

  connect(){
    this.choicesAgentContact = new Choices(this.agent_contactTarget, choicesDefaults);
    this.choicesStructureContact = new Choices(this.structure_contactTarget, choicesDefaults);
    this.updateFilterCounter()

    const sidebarClosingObserver = new MutationObserver((mutations) => {
      mutations.forEach(mutation => {
        if (mutation.type !== "attributes" && mutation.attributeName !== "class") return;
        if (!mutation.target.classList.contains("open")){
          this.updateFilterCounter()
        }
      });
    });
    sidebarClosingObserver.observe(this.sidebarTarget, {attributes: true})
  }
}

applicationReady.then(app => {
  app.register("search-form", SearchFormController)
})
