# /// script
# dependencies = [
#     "faker>=37.0.0,<38.0.0",
#     "polars>=1.38.1,<2.0.0",
#     "ssb-parquedit==0.1.0",
#     "marimo==0.25.0",
#     "marimo-studio==0.2.3",
#     "anywidget==0.11.0",
# ]
# requires-python = ">=3.14,<3.15"
#
# [tool.marimo-studio]
# view_root = "views"
# runtime = "server"
# default = "ssb"
#
# [tool.marimo-studio.cells]
# ///

import marimo

__generated_with = "0.25.0"
app = marimo.App(width="full", app_title="Parqueditor")


@app.cell
def imports_and_mock_data():
    from ssb_parquedit import ParquEdit
    from faker import Faker
    import polars as pl
    import widgets as ds

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

    return LocalParquEdit, ParquEdit, ds, pl


@app.cell
def establish_connection(LocalParquEdit, ParquEdit):
    import os
    import numbers
    import marimo as mo

    reasons = [
        "OTHER_SOURCE",
        "REVIEW",
        "OWNER",
        "MARGINAL_UNIT",
        "DUPLICATE",
        "OTHER",
    ]
    get_refresh, set_refresh = mo.state(0)

    if os.environ.get("DAPLA_ENVIRONMENT", "").upper() == "PROD":
        con = ParquEdit()
    else:
        os.environ["DAPLA_TEAM_NAME"] = "local-mock-team-name"
        os.environ["DAPLA_USER"] = "local-mock-user@ssb.no"
        con = LocalParquEdit.with_mock_tables()
    return con, get_refresh, mo, set_refresh


@app.cell
def check_connection_status(con, mo):
    try:
        tables = con.list_tables()
        connection_error = None
    except Exception as error:
        tables = []
        connection_error = error

    if connection_error:
        status = mo.md(
            "## Kunne ikke koble til Parquedit\n\n"
            "Sjekk:\n\n"
            "- At du har startet tjenesten med riktig team\n"
            "- At Parquedit er skrudd på for teamet i Dapla Ctrl"
        )
    elif not tables:
        status = mo.md(
            "## Fant ingen Parquedit-tabeller\n\n"
            "Sjekk at du har startet tjenesten med riktig team"
        )
    else:
        status = mo.md("")
    status
    return connection_error, tables


@app.cell
def render_dashboard_intro(connection_error, mo, tables):
    mo.stop(connection_error is not None or not tables, mo.md(""))
    mo.md(
        "# Parqueditor\n\n"
        "Velg en Parqedit-tabell, markér en rad tabellen og gjør ønskede endringer.\n"
        "I tabellen kan du søke og filtrere per kolonne."
    )
    return


@app.cell
def render_table_selector(connection_error, ds, mo, tables):
    mo.stop(connection_error is not None or not tables, mo.md(""))
    mo.md(
        "# Parqueditor\n\n"
        "Velg en Parqedit-tabell, markér en rad tabellen og gjør ønskede endringer.\n"
        "I tabellen kan du søke og filtrere per kolonne."
    )
    table_selector = mo.ui.anywidget(
        ds.Dropdown(options=list(tables), selected=tables[0])
    )
    mo.vstack(
        [
            mo.md(f"### Velg Parqueditor-tabell"),
            table_selector,
        ]
    )
    return (table_selector,)


@app.cell
def render_data_table(con, get_refresh, mo, pl, table_selector):
    _ = get_refresh()
    data: pl.DataFrame = con.view(
        table_name=table_selector.selected,
        output_format="polars",
    )
    table_view = mo.ui.table(
        data=data,
        selection="single",
        pagination=True,
        page_size=10,
        label="### Markér raden som skal editeres",
    )
    table_view
    return data, table_view


@app.cell
def render_row_edit_form(data: "pl.DataFrame", ds, mo, pl, table_view):
    selected: pl.DataFrame = table_view.value
    selected_row = selected.row(0, named=True) if selected.height else None

    mo.stop(selected_row is None, mo.md(""))

    input_values = {
        column: selected_row[column] for column in data.columns if column != "rowid"
    }
    input_values["_reason"] = "REVIEW"
    input_values["_comment"] = ""
    edit_form = mo.ui.anywidget(ds.Form(form_data=input_values))
    mo.vstack(
        [
            mo.md(f"### Editér rad med `rowid={selected_row['rowid']}`"),
            edit_form,
        ]
    )
    return edit_form, selected_row


@app.cell
def save_row_changes(
    con,
    data: "pl.DataFrame",
    edit_form,
    get_refresh,
    mo,
    selected_row,
    set_refresh,
    table_selector,
):
    # Read both synced widget properties before stopping so Marimo tracks the
    # form submission as a dependency of this cell.
    submitted = edit_form.submitted
    form_data = edit_form.form_data
    mo.stop(not submitted, mo.md(""))

    changes = {
        column: form_data[column]
        for column in data.columns
        if column != "rowid" and str(form_data[column]) != str(selected_row[column])
    }
    if changes:
        con.edit(
            table_name=table_selector.selected,
            rowid=selected_row["rowid"],
            changes=changes,
            change_event_reason=form_data["_reason"],
            change_comment=form_data["_comment"],
        )
    set_refresh(get_refresh() + 1)
    return


@app.cell
def render_edit_history(con, get_refresh, mo, table_selector):
    _ = get_refresh()
    history = con.get_edits(table_name=table_selector.selected)
    mo.stop(history is None or history.empty, mo.md(""))

    history = history.sort_values("snapshot_time", ascending=False)
    history_view = mo.ui.table(
        history,
        selection=None,
        label="### Endringshistorikk",
        visible_columns=[
            "snapshot_time",
            "old_values",
            "new_values",
            "changed_by",
            "change_event_reason",
            "change_comment",
        ],
        format_mapping={
            "snapshot_time": lambda value: value.strftime("%d.%m.%Y %H:%M")
        },
    )
    history_view
    return


if __name__ == "__main__":
    app.run()
