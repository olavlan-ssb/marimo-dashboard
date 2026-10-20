# /// script
# dependencies = [
#     "duckdb>=1.5.2",
#     "faker>=37.0.0,<38.0.0",
#     "marimo>=0.25.2",
#     "polars>=1.38.1,<2.0.0",
#     "ssb-parquedit==0.1.0",
# ]
# requires-python = ">=3.14,<3.15"
#
# ///

import marimo

__generated_with = "0.25.1"
app = marimo.App(width="full", app_title="Parqueditor")


@app.cell
def imports_and_mock_data():
    import marimo as mo
    from ssb_parquedit import ParquEdit
    from faker import Faker
    import polars as pl

    MOCK_TABLES = ("local_mock_table_1", "local_mock_table_2")
    MOCK_ROW_COUNT = 100

    def make_mock_data(seed: int) -> pl.DataFrame:
        fake = Faker("no_NO")
        fake.seed_instance(seed)
        return pl.DataFrame(
            {
                "record_id": [fake.uuid4() for _ in range(MOCK_ROW_COUNT)],
                "organization_number": [
                    fake.numerify("#########") for _ in range(MOCK_ROW_COUNT)
                ],
                "organization_name": [fake.company() for _ in range(MOCK_ROW_COUNT)],
                "area_code": [fake.postcode() for _ in range(MOCK_ROW_COUNT)],
                "sector_code": [fake.numerify("##") for _ in range(MOCK_ROW_COUNT)],
                "sector": [fake.bs() for _ in range(MOCK_ROW_COUNT)],
                "period": [fake.date(pattern="%Y-%m") for _ in range(MOCK_ROW_COUNT)],
                "number_of_employees": [
                    fake.random_int(min=1, max=5000) for _ in range(MOCK_ROW_COUNT)
                ],
                "income": [
                    float(fake.pyfloat(left_digits=7, right_digits=2, positive=True))
                    for _ in range(MOCK_ROW_COUNT)
                ],
                "status": [fake.word() for _ in range(MOCK_ROW_COUNT)],
                "date": [
                    fake.date_between(start_date="-2y", end_date="today").isoformat()
                    for _ in range(MOCK_ROW_COUNT)
                ],
            }
        )

    class LocalParquEdit(ParquEdit):
        @classmethod
        def with_mock_tables(cls):
            con = cls.local()
            for index, table_name in enumerate(MOCK_TABLES):
                if not con.exists(table_name):
                    con.create_table(
                        table_name,
                        source=make_mock_data(seed=index),
                        product_name="local-mock-statistic",
                        user_defined_id=["record_id"],
                        fill=True,
                    )
            return con

    return LocalParquEdit, mo


@app.cell
def connection(LocalParquEdit):
    parquedit = LocalParquEdit.with_mock_tables()
    return (parquedit,)


@app.cell
def table_picker(mo, parquedit):
    table_names = parquedit.list_tables()
    table_picker = mo.ui.dropdown(
        options=table_names,
        value=table_names[0] if table_names else None,
        label="ParquEdit-tabell",
    )
    return (table_picker,)


@app.cell
def table_view(mo, parquedit, table_picker):
    table_name = table_picker.value
    rows = parquedit.view(table_name, output_format="polars")
    row_picker = mo.ui.dropdown(
        options={str(row["rowid"]): int(row["rowid"]) for row in rows.iter_rows(named=True)},
        value=str(rows[0, "rowid"]) if len(rows) else None,
        label="Rad",
    )
    _table_output = mo.vstack([mo.md(f"### {table_name}"), mo.ui.table(rows), row_picker])
    return row_picker, rows, table_name


@app.cell
def edit_form(mo, row_picker, rows):
    selected = rows.filter(rows["rowid"] == row_picker.value).row(0, named=True)
    fields = {
        column: mo.ui.text(value="" if selected[column] is None else str(selected[column]), label=column)
        for column in rows.columns
        if column != "rowid"
    }
    fields["change_event_reason"] = mo.ui.text(value="correction", label="Endringsårsak")
    fields["change_comment"] = mo.ui.text(label="Kommentar")
    save = mo.ui.button(label="Lagre endring", kind="success")
    form = mo.ui.dictionary(fields).form(show_clear_button=False)
    _edit_output = mo.vstack([mo.md(f"**Valgt rowid:** `{row_picker.value}`"), form, save])
    return form, save


@app.cell
def save_edit(form, mo, parquedit, row_picker, save, table_name):
    if form is not None and save.value:
        values = form.value
        changes = {key: value for key, value in values.items() if key not in {"change_event_reason", "change_comment"}}
        parquedit.edit(
            table_name,
            int(row_picker.value),
            changes,
            values["change_event_reason"],
            values["change_comment"],
        )
        edit_result = mo.md("Endringen er lagret. Velg raden på nytt for å se oppdatert verdi.")
    else:
        edit_result = mo.md("Velg en rad og fyll ut skjemaet for å redigere.")
    return


@app.cell
def history(mo, parquedit, table_name):
    edits = parquedit.get_edits(table_name)
    history_output = mo.vstack([
        mo.md("### Endringshistorikk"),
        mo.ui.table(edits) if not edits.empty else mo.md("Ingen endringer registrert."),
    ])
    return


if __name__ == "__main__":
    app.run()
