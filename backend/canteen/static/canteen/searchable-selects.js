function enhanceSelect(select) {
  if (select.multiple || select.dataset.enhancedSelect === "true") return;
  select.dataset.enhancedSelect = "true";

  const wrapper = document.createElement("div");
  wrapper.className = "search-select";

  const search = document.createElement("input");
  search.type = "search";
  search.className = "search-select-input";
  search.setAttribute("aria-label", `Search ${select.labels[0]?.textContent || select.name}`);
  search.placeholder = "Type to search...";

  const list = document.createElement("div");
  list.className = "search-select-list";
  list.setAttribute("role", "listbox");

  select.classList.add("native-select-hidden");
  select.parentNode.insertBefore(wrapper, select);
  wrapper.appendChild(select);
  wrapper.appendChild(search);
  wrapper.appendChild(list);

  function optionLabel(option) {
    return option.textContent.trim();
  }

  function selectedOption() {
    return select.options[select.selectedIndex];
  }

  function render() {
    const query = search.value.trim().toLowerCase();
    list.innerHTML = "";
    Array.from(select.options)
      .filter((option) => option.value && optionLabel(option).toLowerCase().includes(query))
      .forEach((option) => {
        const button = document.createElement("button");
        button.type = "button";
        button.className = "search-select-option";
        button.setAttribute("role", "option");
        button.setAttribute("aria-selected", option.selected ? "true" : "false");
        button.textContent = optionLabel(option);
        button.addEventListener("click", () => {
          select.value = option.value;
          search.value = optionLabel(option);
          select.dispatchEvent(new Event("change", { bubbles: true }));
          render();
        });
        list.appendChild(button);
      });
  }

  search.addEventListener("input", render);
  search.addEventListener("focus", render);
  search.addEventListener("keydown", (event) => {
    const options = Array.from(list.querySelectorAll(".search-select-option"));
    if (event.key === "ArrowDown" && options.length) {
      event.preventDefault();
      options[0].focus();
    }
  });
  list.addEventListener("keydown", (event) => {
    const options = Array.from(list.querySelectorAll(".search-select-option"));
    const index = options.indexOf(document.activeElement);
    if (event.key === "ArrowDown" && options[index + 1]) {
      event.preventDefault();
      options[index + 1].focus();
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      if (index <= 0) search.focus();
      else options[index - 1].focus();
    }
  });

  const initial = selectedOption();
  if (initial && initial.value) search.value = optionLabel(initial);
  render();
}

document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll('select[data-searchable-select="true"]').forEach(enhanceSelect);
});
