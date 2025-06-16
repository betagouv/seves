import {setUpFreeLinks} from "/static/core/free_links.js";
import {patchItems, findPath, tsDefaultOptions} from "/static/ssa/_custom_tree_select.js"

document.addEventListener('DOMContentLoaded', () => {
  function disableSourceOptions(typeEvenementInput, sourceInput, reset=true) {
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
    if (reset===true){
      sourceInput.selectedIndex = 0;
    }
  }

  function setupCategorieProduit(){
    const options = JSON.parse(document.getElementById("categorie-produit-data").textContent)
    const selectedValue = document.getElementById("id_categorie_produit").value
    const treeselect = new Treeselect({
      parentHtmlContainer: document.getElementById("categorie-produit"),
      value: selectedValue,
      options: options,
      isSingleSelect: true,
      openCallback() {
        patchItems(treeselect.srcElement)
      },
      ...tsDefaultOptions
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

  function handleValueChangeCategorieDanger(value, options){
    const fullPath = findPath(value, options).map(n => n.name).join(' > ')

    document.getElementById("id_categorie_danger").value = value
    document.querySelector("#categorie-danger .treeselect-input__tags-count").innerText = fullPath
    if(fullPath.includes("Bactérie >")){
      document.getElementById("pam-container").classList.remove("fr-hidden")
    } else {
      document.getElementById("pam-container").classList.add("fr-hidden")
    }
  }

  function setupCategorieDanger(){
    const options = JSON.parse(document.getElementById("categorie-danger-data").textContent)
    const selectedValue = document.getElementById("id_categorie_danger").value
    const treeselect = new Treeselect({
      parentHtmlContainer: document.getElementById("categorie-danger"),
      value: selectedValue,
      options: options,
      isSingleSelect: true,
      openCallback() {
        patchItems(treeselect.srcElement)
        if (this._customHeaderAdded) {
          treeselect.srcElement.querySelectorAll(".categorie-danger-header").forEach(el => {
            el.removeAttribute("hidden");
            el.removeAttribute("aria-hidden");
          })
          return;
        }
        const list = document.querySelector("#categorie-danger .treeselect-list")
        if (list) {
          const clone = document.getElementById('categorie-danger-header').cloneNode(true);
          clone.id = ''
          clone.classList.remove('fr-hidden')
          clone.classList.add("categorie-danger-header")
          list.prepend(clone);
          this._customHeaderAdded = true

          document.querySelector("#categorie-danger .treeselect-list").addEventListener("click", (event) => {
            if (event.target.firstElementChild && event.target.firstElementChild.classList.contains("shortcut")) {
              const value = event.target.firstElementChild.textContent.trim()
              treeselect.updateValue(value)
              treeselect.toggleOpenClose();
              handleValueChangeCategorieDanger(value, options)
            }
          });
        }
      },
      searchCallback(item) {
        if (item.length === 0) {
          treeselect.srcElement.querySelectorAll(".categorie-danger-header").forEach(el => {
            el.removeAttribute("hidden");
            el.removeAttribute("aria-hidden");
          })
        } else {
          treeselect.srcElement.querySelectorAll(".categorie-danger-header").forEach(el => {
            el.setAttribute("hidden", "hidden");
            el.setAttribute("aria-hidden", "true");
          })
        }
      },
      ...tsDefaultOptions
    })
    document.querySelector("#categorie-danger .treeselect-input").classList.add("fr-input")
    treeselect.srcElement.addEventListener("update-dom", ()=>{patchItems(treeselect.srcElement)})
    treeselect.srcElement.addEventListener('input', (e) => {
      if (!!e.detail){
        handleValueChangeCategorieDanger(e.detail, options)
      } else {
        document.getElementById("pam-container").classList.add("fr-hidden")
      }
    })
  }

  const typeEvenementInput = document.getElementById('id_type_evenement')
  const sourceInput = document.getElementById('id_source')
  typeEvenementInput.addEventListener("change", () => {
    disableSourceOptions(typeEvenementInput, sourceInput)
  })
  disableSourceOptions(typeEvenementInput, sourceInput, false)
  setUpFreeLinks(document.getElementById("id_free_link"), document.getElementById('free-links-id'))
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
