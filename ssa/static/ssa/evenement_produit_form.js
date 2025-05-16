import {setUpFreeLinks} from "/static/core/free_links.js";

function findPath(value, options, path = []) {
  for (const node of options) {
    if (node.value === value) {
      return [...path, node];
    }
    if (node.children) {
      const result = findPath(value, node.children, [...path, node]);
      if (result) return result;
    }
  }
  return null;
}

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

  const categorieProduitInput = document.getElementById("categorie-produit")
  const options = JSON.parse(document.getElementById("categorie-produit-data").textContent)
  const treeselect = new Treeselect({
    parentHtmlContainer: categorieProduitInput,
    value: null,
    options: JSON.parse(document.getElementById("categorie-produit-data").textContent),
    isSingleSelect: true,
    showTags: false,
    placeholder: "Choisir",
  })
  document.querySelector("#categorie-produit .treeselect-input").classList.add("fr-input")

  treeselect.srcElement.addEventListener('input', (e) => {
    const result = findPath(e.detail, options)
    document.getElementById("id_categorie_produit").value = e.detail
    document.querySelector("#categorie-produit .treeselect-input__tags-count").innerText = result.map(n => n.name).join(' > ')
  })
});
