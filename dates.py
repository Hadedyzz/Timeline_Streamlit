import pandas as pd
from datetime import datetime

def parse_datetimes(df):
    """
    Combine Date (DD.MM) with StartTime/EndTime (HH:MM), year is always 2025.
    Returns (start_dt, end_dt) as pd.Series.
    """
    def combine(row, col):
        try:
            date_str = str(row["Date"])
            if "." in date_str:
                day, month = date_str.split(".")
                date_part = datetime(year=2025, month=int(month), day=int(day))
            else:
                return pd.NaT
            time_part = pd.to_datetime(str(row[col]), format="%H:%M", errors="coerce").time()
            if pd.isnull(time_part):
                return pd.NaT
            return datetime.combine(date_part.date(), time_part)
        except Exception:
            return pd.NaT
    start_dt = df.apply(lambda row: combine(row, "StartTime"), axis=1)
    end_dt = df.apply(lambda row: combine(row, "EndTime"), axis=1)
    return (start_dt, end_dt)
