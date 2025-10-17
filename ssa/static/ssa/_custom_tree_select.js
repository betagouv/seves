import "TreeSelect"

export function patchItems(element){
    setTimeout(() => {
        element.querySelectorAll('.treeselect-list__item').forEach(itemElement => {

      // Show checkbox / radio is the element can be selected
            if (!itemElement.classList.contains("treeselect-list__item--non-selectable-group")){
                const checkboxContainer = itemElement.querySelector(".treeselect-list__item-checkbox-container")
                if (!!checkboxContainer){
                    checkboxContainer.style.display = "initial"
                }
            }

            const iconElement =  itemElement.querySelector(".treeselect-list__item-icon")
            if (!iconElement) {
                return
            }

      // If element has children hide the label (which triggers on click the selection of the element)
      // and copy the text from the label next to the icon (which triggers on click the opening/closing of the group)
            const label = itemElement.querySelector(".treeselect-list__item-label")
            label.style.display = "none"
            if (iconElement.innerHTML.includes(label.innerText)) return;
            iconElement.innerHTML += label.innerText
        });
    }, 0);
}

export function findPath(value, options, path = []) {
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

export function addLevel2CategoryIfAllChildrenAreSelected(options, selectedOptions){
    const result = [...selectedOptions]

    options.forEach(level1 => {
        level1.children.forEach(level2 => {
            const level3Ids = level2.children .map(c => c.value)
            if (level3Ids.length && level3Ids.every(value => selectedOptions.includes(value))) {
                if (!result.includes(level2.value)) {
                    result.push(level2.value);
                }
            }
        });
    });
    return result
}

export function isLevel2WithChildren(data, value) {
    for (const item of data) {
        for (const child of item.children || []) {
            if (child.value === value) {
                return child.children && child.children.length > 0;
            }
        }
    }
    return false;
}

export function showHeader(element, headerClass){
    element.querySelectorAll(headerClass).forEach(el => {
        el.removeAttribute("hidden");
        el.removeAttribute("aria-hidden");
    })
}
export function hideHeader(element, headerClass){
    element.querySelectorAll(headerClass).forEach(el => {
        el.setAttribute("hidden", "hidden");
        el.setAttribute("aria-hidden", "true");
    })
}


export function shortcutClicked(event, treeselect, input){
    const label = event.target.getElementsByTagName("label")[0]
    const value = label.textContent.trim()
    const checkbox = treeselect.srcElement.querySelector('[id$=' + label.getAttribute("for") + ']')
    checkbox.checked = !checkbox.checked

    let valuesToSet = treeselect.value
    if (checkbox.checked){
        valuesToSet.push(value)
    } else {
        valuesToSet.pop(value)
    }

    treeselect.updateValue(valuesToSet)
    input.value = valuesToSet.join("||")
    let text = ""
    if (valuesToSet.length === 1){
        text = valuesToSet[0]
    } else {
        text = `${valuesToSet.length} ${treeselect.tagsCountText}`
    }
    treeselect.srcElement.querySelector(".treeselect-input__tags-count").innerText = text
}

export const tsDefaultOptions = {
    showTags: false,
    clearable: false,
    placeholder: "Choisir",
    emptyText: "Pas de résultat",
    direction: "bottom",
    tagsCountText: "éléments sélectionnés"
}
