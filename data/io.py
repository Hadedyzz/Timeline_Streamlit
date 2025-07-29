import pandas as pd
import os
import io

DATA_FILE = "events_last_saved.xlsx"

def load_data_from_file(filepath):
    return pd.read_excel(filepath)

def load_data(uploaded_file=None):
    if uploaded_file is not None:
        df = load_data_from_file(uploaded_file)
    elif os.path.exists(DATA_FILE):
        df = load_data_from_file(DATA_FILE)
    else:
        df = pd.DataFrame(columns=[
            "Date", "StartTime", "EndTime", "Category", "Title", "Description",
            "Scrap (m²)", "B-Grade (m²)", "Reserved", "Cost (€)"
        ])
    # Ensure columns exist
    for col in ["Date", "StartTime", "EndTime"]:
        if col not in df.columns:
            df[col] = ""
    # Remove any legacy columns if present
    for col in ["Start", "End", "Time"]:
        if col in df.columns:
            df = df.drop(columns=[col])
    # Reorder columns to ensure correct order
    cols = df.columns.tolist()
    for col in ["Date", "StartTime", "EndTime"]:
        if col in cols:
            cols.remove(col)
    df = df[["Date", "StartTime", "EndTime"] + cols]
    return df

def save_data(df):
    df.to_excel(DATA_FILE, index=False)

def get_blank_excel_bytes():
    empty_df = pd.DataFrame(columns=[
        "Date", "StartTime", "EndTime", "Category", "Title", "Description",
        "Scrap (m²)", "B-Grade (m²)", "Reserved", "Cost (€)"
    ])
    buf = io.BytesIO()
    empty_df.to_excel(buf, index=False)
    return buf.getvalue()
