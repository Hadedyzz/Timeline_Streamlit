import streamlit as st
import pandas as pd
from datetime import datetime
from utils.colors import CATEGORY_OPTIONS, CATEGORY_COLOR_MAP, assign_colors, get_color
from data.io import load_data, save_data, get_blank_excel_bytes
from parsing.dates import parse_datetimes
from plots.timeline import plot_timeline, compute_timeline
from plots.pareto import plot_dynamic_pareto_by_title, plot_dynamic_pareto_scrap_bgrade_by_title
from utils.branding import add_logo_to_fig
import io

st.set_page_config(page_title="Timeline Dashboard", layout="wide")
st.title("📅 Timeline Dashboard")

with st.sidebar:
    st.header("Data")
    uploaded_file = st.file_uploader("Load Data (.xlsx)", type=["xlsx"])
    # Load file button
    if st.button("Load File") and uploaded_file:
        df = load_data(uploaded_file)
        st.session_state["df"] = df
        st.success("File loaded.")
    # If no event table, start with blank
    elif "df" not in st.session_state:
        df = pd.DataFrame(columns=[
            "Date", "StartTime", "EndTime", "Category", "Title", "Description", "Current Status",
            "Scrap (m²)", "B-Grade (m²)", "Reserved", "Cost (€)", "Countermeasures"
        ])
        st.session_state["df"] = df
    else:
        df = st.session_state["df"]

    # Download current event table as Excel
    if st.button("Download Current Event Table"):
        if "df" in st.session_state:
            buf = io.BytesIO()
            st.session_state["df"].to_excel(buf, index=False)
            st.download_button(
                "Download Event Table as Excel",
                data=buf.getvalue(),
                file_name="timeline_eventtable.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    # Create new Excel file with prompt to save current table
    if st.button("Create New Excel File"):
        if not st.session_state["df"].empty:
            st.warning("You have unsaved data in the event table. Please download it before creating a new blank file.")
            if st.button("Download & Continue"):
                buf = io.BytesIO()
                st.session_state["df"].to_excel(buf, index=False)
                st.download_button(
                    "Download Event Table as Excel",
                    data=buf.getvalue(),
                    file_name="timeline_eventtable.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
                # Clear event table after download
                st.session_state["df"] = pd.DataFrame(columns=[
                    "Date", "StartTime", "EndTime", "Category", "Title", "Description", "Current Status",
                    "Scrap (m²)", "B-Grade (m²)", "Reserved", "Cost (€)", "Countermeasures"
                ])
                st.info("Event table cleared. You can now download a blank Excel file.")
                st.download_button(
                    "Download Blank Excel",
                    data=get_blank_excel_bytes(),
                    file_name="timeline_blank.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
        else:
            st.download_button(
                "Download Blank Excel",
                data=get_blank_excel_bytes(),
                file_name="timeline_blank.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

category_filter = st.multiselect("Filter by Category", df["Category"].dropna().unique())
reserved_filter = st.selectbox("Filter Reserved", ["All", "Yes", "No"])
filtered_df = df.copy()
if category_filter:
    filtered_df = filtered_df[filtered_df["Category"].isin(category_filter)]
if reserved_filter != "All":
    filtered_df = filtered_df[
        filtered_df["Reserved"].astype(str).str.strip().str.lower().isin(
            ["yes"] if reserved_filter == "Yes" else ["no"]
        )
    ]

with st.form("timeline_form"):
    st.subheader("Event Table")
    editable_df = filtered_df.copy()
    if "Date" in editable_df.columns:
        editable_df["Date"] = editable_df["Date"].astype(str).str[:5]
    for col in ["StartTime", "EndTime"]:
        if pd.api.types.is_float_dtype(editable_df[col]) or pd.api.types.is_integer_dtype(editable_df[col]):
            editable_df[col] = editable_df[col].astype("object")
        if pd.api.types.is_datetime64_any_dtype(editable_df[col]):
            editable_df[col] = editable_df[col].dt.strftime("%H:%M")
        editable_df[col] = editable_df[col].astype(str).str[:5]
        editable_df.loc[editable_df[col] == "nan", col] = ""
    start_dt, end_dt = parse_datetimes(editable_df)
    duration = end_dt - start_dt
    duration_minutes = duration.apply(lambda x: x.total_seconds() / 60 if pd.notnull(x) else None)
    editable_df["Duration (min)"] = pd.to_numeric(duration_minutes, errors="coerce").round().astype("Int64")
    cols = editable_df.columns.tolist()
    for col in ["Date", "StartTime", "EndTime"]:
        if col in cols:
            cols.remove(col)
    if "Duration (min)" in cols:
        cols.remove("Duration (min)")
    editable_df = editable_df[["Date", "StartTime", "EndTime", "Duration (min)"] + cols]
    edited_df = st.data_editor(
        editable_df,
        num_rows="dynamic",
        use_container_width=True,
        key="data_editor",
        column_config={
            "Date": st.column_config.TextColumn(
                "Date",
                help="Format: DD.MM (year is always 2025)"
            ),
            "Category": st.column_config.SelectboxColumn(
                "Category",
                options=CATEGORY_OPTIONS
            ),
            "StartTime": st.column_config.TextColumn(
                "StartTime",
                help="Format: HH:MM"
            ),
            "EndTime": st.column_config.TextColumn(
                "EndTime",
                help="Format: HH:MM"
            ),
            "Duration (min)": st.column_config.NumberColumn(
                "Duration (min)",
                help="Automatically calculated from EndTime - StartTime",
                disabled=True
            ),
        }
    )
    if edited_df[["Date", "StartTime", "EndTime", "Category"]].isnull().any().any():
        st.warning("Some rows are missing required fields like Date, StartTime, EndTime, or Category.")
    all_categories = edited_df["Category"].dropna().unique()
    color_map = CATEGORY_COLOR_MAP.copy()
    missing = [cat for cat in all_categories if cat not in color_map]
    if missing:
        color_map.update(assign_colors(missing))
    col1, col2, col3, col4, col5, col6, col7 = st.columns(7)
    with col1:
        view_mode = st.selectbox("Timeline View", ["Day", "Week", "Month"])
    with col2:
        today = datetime.now().date()
        selected_date = st.date_input("Select Date", today, format="DD.MM.YYYY")
    with col3:
        update_clicked = st.form_submit_button("Update Views")
    with col4:
        show_title = st.toggle("Show Title", value=True)
    with col5:
        show_minutes = st.toggle("Show Minutes", value=True)
    with col6:
        show_scrap = st.toggle("Show Scrap", value=True)
    with col7:
        show_costs = st.toggle("Show Costs", value=True)
    show_reserved = st.toggle("Show Reserved", value=True)

if update_clicked:
    start_dt, end_dt = parse_datetimes(edited_df)
    duration = end_dt - start_dt
    duration_minutes = duration.apply(lambda x: x.total_seconds() / 60 if pd.notnull(x) else None)
    edited_df["Duration (min)"] = pd.to_numeric(duration_minutes, errors="coerce").round().astype("Int64")
    st.session_state["df"] = edited_df.copy()
    save_data(edited_df)
    with st.spinner("Building timeline…"):
        fig = plot_timeline(
            st.session_state["df"],
            view_mode,
            selected_date,
            color_map,
            show_title=show_title,
            show_minutes=show_minutes,
            show_scrap=show_scrap,
            show_costs=show_costs,
            show_reserved=show_reserved
        )
    st.session_state["timeline_fig"] = fig
    st.success("Timeline updated!")

all_categories = st.session_state["df"]["Category"].dropna().unique()
color_map = CATEGORY_COLOR_MAP.copy()
missing = [cat for cat in all_categories if cat not in color_map]
if missing:
    color_map.update(assign_colors(missing))

st.header("Timeline")
if "timeline_fig" in st.session_state:
    st.plotly_chart(st.session_state["timeline_fig"], use_container_width=True)
else:
    today = datetime.now().date()
    fig = plot_timeline(
        st.session_state["df"],
        "Day",
        today,
        color_map,
        show_title=True,
        show_minutes=True,
        show_scrap=True,
        show_costs=True,
        show_reserved=True
    )
    st.session_state["timeline_fig"] = fig
    st.plotly_chart(fig, use_container_width=True)

# Pareto charts filtered by timeline view and dynamic title
st.header(f"Pareto by Cost (€) - {view_mode} {selected_date}")
st.plotly_chart(plot_dynamic_pareto_by_title(st.session_state["df"], "Cost (€)", view_mode, selected_date, color_map), use_container_width=True)

st.header(f"Pareto by Scrap + B-Grade - {view_mode} {selected_date}")
st.plotly_chart(plot_dynamic_pareto_scrap_bgrade_by_title(st.session_state["df"], view_mode, selected_date, color_map), use_container_width=True)

