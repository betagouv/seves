import {setUpFreeLinks} from "/static/core/free_links.js";
import {patchItems, findPath} from "/static/ssa/_custom_tree_select.js"

document.addEventListener('DOMContentLoaded', () => {
  function disableSourceOptions(typeEvenementInput, sourceInput) {
    const isHumanCase = typeEvenementInput.value === "investigation_cas_humain";
    sourceInput.querySelectorAll('option').forEach(option => {
      if (option.value !== "autre") {
        if ((option.getAttribute('data-for-human-case') === 'true') !== isHumanCase){
          option.style.display = 'none'
        } else {
          option.style.display = ''
        }
      }
    });
    sourceInput.selectedIndex = 0;
  }

  function setupCategorieProduit(){
    const options = JSON.parse(document.getElementById("categorie-produit-data").textContent)
    const treeselect = new Treeselect({
      parentHtmlContainer: document.getElementById("categorie-produit"),
      value: null,
      options: options,
      isSingleSelect: true,
      showTags: false,
      placeholder: "Choisir",
      openCallback() {
        patchItems(treeselect.srcElement)
      },
    })
    patchItems(treeselect.srcElement)
    treeselect.srcElement.addEventListener("update-dom", ()=>{patchItems(treeselect.srcElement)})
    document.querySelector("#categorie-produit .treeselect-input").classList.add("fr-input")

    treeselect.srcElement.addEventListener('input', (e) => {
      if (!e.detail) return
      const result = findPath(e.detail, options)
      document.getElementById("id_categorie_produit").value = e.detail
      document.querySelector("#categorie-produit .treeselect-input__tags-count").innerText = result.map(n => n.name).join(' > ')
    })
  }

  function setupCategorieDanger(){
    const options = JSON.parse(document.getElementById("categorie-danger-data").textContent)
    const treeselect = new Treeselect({
      parentHtmlContainer: document.getElementById("categorie-danger"),
      value: null,
      options: options,
      isSingleSelect: true,
      showTags: false,
      placeholder: "Choisir",
      openCallback() {
        patchItems(treeselect.srcElement)
        if (this._customHeaderAdded) return;
        const list = document.querySelector("#categorie-danger .treeselect-list")
        if (list) {
          const clone = document.getElementById('categorie-danger-header').cloneNode(true);
          clone.id = ''
          clone.classList.remove('fr-hidden')
          list.prepend(clone);
          this._customHeaderAdded = true

          document.querySelector("#categorie-danger .treeselect-list").addEventListener("click", (event) => {
            if (event.target.firstElementChild && event.target.firstElementChild.classList.contains("shortcut")) {
              const value = event.target.firstElementChild.textContent.trim()
              treeselect.updateValue(value)
              treeselect.toggleOpenClose();
              const result = findPath(value, options)
              document.getElementById("id_categorie_danger").value = value
              document.querySelector("#categorie-danger .treeselect-input__tags-count").innerText = result.map(n => n.name).join(' > ')
            }
          });

        }
      }
    })
    document.querySelector("#categorie-danger .treeselect-input").classList.add("fr-input")
    treeselect.srcElement.addEventListener("update-dom", ()=>{patchItems(treeselect.srcElement)})

    treeselect.srcElement.addEventListener('input', (e) => {
      if (!e.detail) return
      const result = findPath(e.detail, options)
      document.getElementById("id_categorie_danger").value = e.detail
      document.querySelector("#categorie-danger .treeselect-input__tags-count").innerText = result.map(n => n.name).join(' > ')
    })
  }

  const typeEvenementInput = document.getElementById('id_type_evenement')
  const sourceInput = document.getElementById('id_source')
  typeEvenementInput.addEventListener("change", () => {
    disableSourceOptions(typeEvenementInput, sourceInput)
  })
  disableSourceOptions(typeEvenementInput, sourceInput)
  setUpFreeLinks(document.getElementById("id_free_link"), null)
  new Choices(document.getElementById("id_quantification_unite"), {
    classNames: {
      containerInner: 'fr-select',
    },
    itemSelectText: '',
    position: 'bottom',
    shouldSort: false,
  });
  setupCategorieProduit()
  setupCategorieDanger()
});
