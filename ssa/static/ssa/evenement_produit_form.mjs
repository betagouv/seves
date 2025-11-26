import choicesDefaults from "choicesDefaults"
import {setUpFreeLinks} from "/static/core/free_links.js";
import {patchItems, findPath, tsDefaultOptions, isLevel2WithChildren} from "CustomTreeSelect"

document.addEventListener('DOMContentLoaded', () => {
  function handleNoticeProduitDisplay(options, value) {
    if(isLevel2WithChildren(options, value)){
      document.querySelector("#notice-container-produit").classList.remove("fr-hidden")
    } else {
      document.querySelector("#notice-container-produit").classList.add("fr-hidden")
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

    treeselect.srcElement.addEventListener('input', (e) => {handleNoticeProduitDisplay(options, e.detail)})
    handleNoticeProduitDisplay(options, selectedValue)
  }


  setUpFreeLinks(document.getElementById("id_free_link"), document.getElementById('free-links-id'))
  new Choices(document.getElementById("id_quantification_unite"), {
    ...choicesDefaults,
    position: 'bottom',
  });
  setupCategorieProduit()
});
