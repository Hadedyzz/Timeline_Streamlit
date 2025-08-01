import pandas as pd
import os
import io

DATA_FILE = "events_last_saved.xlsx"

def load_data_from_file(filepath):
    return pd.read_excel(filepath)

def load_data(uploaded_file=None):
    if uploaded_file is not None:
        df = load_data_from_file(uploaded_file)
    else:
        df = pd.DataFrame(columns=[
            "Date", "StartTime", "EndTime", "Category", "Title", "Description",
            "Current Status", "Scrap (m²)", "B-Grade (m²)", "Reserved", "Cost (€)", "Countermeasures"
        ])
    # Ensure columns exist
    for col in ["Date", "StartTime", "EndTime", "Category", "Title", "Description", "Current Status", "Scrap (m²)", "B-Grade (m²)", "Reserved", "Cost (€)", "Countermeasures"]:
        if col not in df.columns:
            df[col] = ""
    # Remove any legacy columns if present
    for col in ["Start", "End", "Time"]:
        if col in df.columns:
            df = df.drop(columns=[col])
    # Reorder columns to ensure correct order
    ordered_cols = [
        "Date", "StartTime", "EndTime", "Category", "Title", "Description", "Current Status",
        "Scrap (m²)", "B-Grade (m²)", "Reserved", "Cost (€)", "Countermeasures"
    ]
    # Only keep columns that exist in df
    ordered_cols = [col for col in ordered_cols if col in df.columns]
    df = df[ordered_cols]
    return df

def save_data(df):
    pass  # No longer used

def get_blank_excel_bytes():
    empty_df = pd.DataFrame(columns=[
        "Date", "StartTime", "EndTime", "Category", "Title", "Description", "Current Status",
        "Scrap (m²)", "B-Grade (m²)", "Reserved", "Cost (€)", "Countermeasures"
    ])
    buf = io.BytesIO()
    empty_df.to_excel(buf, index=False)
    return buf.getvalue()
