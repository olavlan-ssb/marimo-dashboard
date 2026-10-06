function render({ model, el }) {
  function renderForm() {
    el.replaceChildren();

    if (model.get("submitted")) {
      return;
    }

    let form = document.createElement("form");
    let fields = new Map();

    for (const [key, value] of Object.entries(model.get("form_data"))) {
      let field = document.createElement("div");
      field.classList.add("ds-field");

      let label = document.createElement("label");
      label.classList.add("ds-label");
      label.htmlFor = `form-input-${key}`;
      label.textContent = key;

      let input = document.createElement("input");
      input.classList.add("ds-input");
      input.type = "text";
      input.id = label.htmlFor;
      input.name = key;
      input.value = value ?? "";

      fields.set(key, input);
      field.append(label, input);
      form.appendChild(field);
    }

    let submit = document.createElement("button");
    submit.classList.add("ds-button");
    submit.type = "submit";
    submit.textContent = "Submit";
    form.appendChild(submit);

    form.addEventListener("submit", (event) => {
      event.preventDefault();
      let value = {};
      for (const [key, input] of fields) {
        value[key] = input.value;
      }
      model.set("form_data", value);
      model.set("submitted", true);
      model.save_changes();
      renderForm();
    });

    el.appendChild(form);
  }

  model.on("change:submitted", renderForm);
  renderForm();
}

export default { render };
