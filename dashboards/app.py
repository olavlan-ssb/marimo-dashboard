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
def table_selector(mo, parquedit):
    table_selector_output = mo.ui.dropdown(
        options=parquedit.list_tables(),
        label="ParquEdit-tabell",
    )
    table_selector_output
    return (table_selector_output,)


@app.cell
def table_view(mo, parquedit, table_selector_output):
    import polars as _pl

    _selected_table_name = table_selector_output.value
    if _selected_table_name:
        selected_table_data = parquedit.view(
            _selected_table_name, output_format="polars"
        )
        table_view_output = mo.ui.table(selected_table_data)
    else:
        selected_table_data = _pl.DataFrame()
        table_view_output = mo.md("Velg en tabell.")
    table_view_output
    return (selected_table_data,)


@app.cell
def row_editor(mo, selected_table_data, table_selector_output):
    import polars as _pl

    _selected_table_name = table_selector_output.value
    if _selected_table_name and selected_table_data.height:
        first_row = selected_table_data.row(0, named=True)
        editor_controls = {
            "rowid": mo.ui.number(
                start=0,
                stop=max(int(selected_table_data["rowid"].max()), 0),
                value=int(first_row["rowid"]),
                label="rowid",
            ),
        }
        for _column_name, _column_value in first_row.items():
            if _column_name != "rowid":
                editor_controls[_column_name] = mo.ui.text(
                    value="" if _column_value is None else str(_column_value),
                    label=_column_name,
                )
        row_editor_output = mo.ui.form(
            mo.ui.dictionary(editor_controls),
            submit_button_label="Lagre rad",
            show_clear_button=False,
        )
    else:
        row_editor_output = mo.md("Velg en tabell med data for å redigere en rad.")
    row_editor_output
    return (row_editor_output,)


@app.cell
def save_row(
    mo,
    parquedit,
    row_editor_output,
    selected_table_data,
    table_selector_output,
):
    import polars as _pl

    save_message = None
    if hasattr(row_editor_output, "value") and row_editor_output.value:
        submitted_values = row_editor_output.value
        _selected_table_name = table_selector_output.value
        rowid = int(submitted_values.pop("rowid"))
        original_row = selected_table_data.filter(_pl.col("rowid") == rowid).row(
            0, named=True
        )
        changes = {}
        for _column_name, _new_value in submitted_values.items():
            _column_type = selected_table_data.schema[_column_name]
            _converted_value = _pl.Series([_new_value]).cast(_column_type).item()
            if _converted_value != original_row[_column_name]:
                changes[_column_name] = _converted_value
        if changes:
            parquedit.edit(
                _selected_table_name,
                rowid,
                changes,
                change_event_reason="interactive_edit",
                change_comment="Rad redigert i ParquEdit-dashboardet",
            )
            save_message = mo.md("Rad lagret.")
        else:
            save_message = mo.md("Ingen endringer å lagre.")
    if save_message:
        save_message
    return


@app.cell
def change_history(mo, parquedit, table_selector_output):
    _selected_table_name = table_selector_output.value
    if _selected_table_name:
        history_data = parquedit.get_edits(_selected_table_name)
        history_output = mo.ui.table(history_data)
    else:
        history_output = mo.md("Velg en tabell for å se endringshistorikken.")
    mo.md("### Endringshistorikk")
    history_output
    return


if __name__ == "__main__":
    app.run()
