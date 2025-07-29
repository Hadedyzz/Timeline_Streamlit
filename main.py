import streamlit as st
import pandas as pd
from datetime import datetime
from utils.colors import CATEGORY_OPTIONS, CATEGORY_COLOR_MAP, assign_colors, get_color
from data.io import load_data, save_data, get_blank_excel_bytes
from parsing.dates import parse_datetimes
from plots.timeline import plot_timeline, compute_timeline
from plots.pareto import plot_dynamic_pareto_by_title, plot_dynamic_pareto_scrap_bgrade_by_title
from utils.branding import add_logo_to_fig

st.set_page_config(page_title="Timeline Dashboard", layout="wide")
st.title("📅 Timeline Dashboard")

with st.sidebar:
    st.header("Data")
    uploaded_file = st.file_uploader("Load Data (.xlsx)", type=["xlsx"])
    if st.button("Create New Excel File"):
        st.download_button(
            "Download Blank Excel",
            data=get_blank_excel_bytes(),
            file_name="timeline_blank.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    if st.button("Load File") and uploaded_file:
        df = load_data(uploaded_file)
        st.session_state["df"] = df
    elif "df" not in st.session_state:
        df = load_data()
        st.session_state["df"] = df
    else:
        df = st.session_state["df"]
    if st.button("Save Data"):
        save_data(df)
        st.success("Data saved.")

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
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        view_mode = st.selectbox("Timeline View", ["Day", "Week", "Month"])
    with col2:
        today = datetime.now().date()
        selected_date = st.date_input("Select Date", today, format="DD.MM.YYYY")
    with col3:
        update_clicked = st.form_submit_button("Update Views")
    with col4:
        show_description = st.toggle("Show Block Descriptions", value=True)

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
            show_description=show_description
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
        show_description=True
    )
    st.session_state["timeline_fig"] = fig
    st.plotly_chart(fig, use_container_width=True)

# Pareto charts filtered by timeline view and dynamic title
st.header(f"Pareto by Cost (€) - {view_mode} {selected_date}")
st.plotly_chart(plot_dynamic_pareto_by_title(st.session_state["df"], "Cost (€)", view_mode, selected_date, color_map), use_container_width=True)

st.header(f"Pareto by Scrap + B-Grade - {view_mode} {selected_date}")
st.plotly_chart(plot_dynamic_pareto_scrap_bgrade_by_title(st.session_state["df"], view_mode, selected_date, color_map), use_container_width=True)


