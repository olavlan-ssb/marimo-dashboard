function render({ model, el }) {
  let options = () => model.get("options");
  let field = document.createElement("div");
  field.classList.add("ds-field");

  let label = document.createElement("label");
  label.classList.add("ds-label");
  label.textContent = "Mock dataset";

  let select = document.createElement("select");
  select.classList.add("ds-input");

  function renderOptions() {
    select.replaceChildren(
      ...options().map((option) => {
        let element = document.createElement("option");
        element.value = option;
        element.textContent = option;
        return element;
      }),
    );
    select.value = model.get("selected");
  }

  select.addEventListener("change", () => {
    model.set("selected", select.value);
    model.save_changes();
  });
  model.on("change:options", () => {
    renderOptions();
  });
  model.on("change:selected", () => {
    select.value = model.get("selected");
  });

  renderOptions();
  field.appendChild(label);
  field.appendChild(select);
  el.appendChild(field);
}

export default { render };
