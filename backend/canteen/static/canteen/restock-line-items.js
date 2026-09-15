function renumberRestockRow(row, rowNumber) {
  row.querySelectorAll("label, input, select").forEach((element) => {
    if (element.htmlFor) element.htmlFor = element.htmlFor.replace("__prefix__", rowNumber);
    if (element.id) element.id = element.id.replace("__prefix__", rowNumber);
    if (element.name) element.name = element.name.replace("__prefix__", rowNumber);
  });
}

document.addEventListener("DOMContentLoaded", () => {
  const table = document.querySelector("[data-restock-line-table]");
  const template = document.querySelector("#restock-line-template");
  const addButton = document.querySelector("[data-add-restock-line]");
  if (!table || !template || !addButton) return;

  addButton.addEventListener("click", () => {
    const tbody = table.querySelector("tbody");
    const nextRowNumber = tbody.querySelectorAll("tr").length + 1;
    const fragment = template.content.cloneNode(true);
    const row = fragment.querySelector("tr");
    renumberRestockRow(row, nextRowNumber);
    tbody.appendChild(fragment);
    row.querySelectorAll('select[data-searchable-select="true"]').forEach((select) => {
      if (window.enhanceSearchableSelect) window.enhanceSearchableSelect(select);
    });
    row.querySelector(".search-select-input")?.focus();
  });
});