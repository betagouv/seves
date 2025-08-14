import {Controller} from "Stimulus";
import Choices from "Choices";
import {applicationReady} from "Application";

// DOM attendu :
// <div data-controller="free-links" data-free-links-ids-value='{{ form.instance.free_link_ids }}'>
//   {{ form.free_link|set_data:"free-links-target:select"  }}
// </div>
//
class FreeLinksController extends Controller {
  static targets = ["select"]
  static values = {
    ids: Array
  }

  connect() {
    this.freeLinksChoices = new Choices(this.selectTarget, {
      searchResultLimit: 500,
      classNames: {
        containerInner: 'fr-select',
      },
      removeItemButton: true,
      shouldSort: false,
      itemSelectText: '',
      noResultsText: 'Aucun résultat trouvé',
      noChoicesText: 'Aucune fiche à sélectionner',
      searchFields: ['label'],
    })

    if (this.hasIdsValue) {
      this.idsValue.forEach(value => {
        this.freeLinksChoices.setChoiceByValue(value)
      })
    }
  }
}

applicationReady.then(app => {
  app.register("free-links", FreeLinksController)
})
