import plotly.graph_objects as go
import pandas as pd
import os
from utils.branding import add_logo_to_fig

def plot_pareto(df, value_col, title, color_map):
    df = df.copy()
    df = df[df["Category"].notnull()]
    df[value_col] = pd.to_numeric(df[value_col], errors="coerce").fillna(0)
    agg = df.groupby("Category")[value_col].sum().sort_values(ascending=False)
    bar_colors = [color_map.get(cat, "#888888") for cat in agg.index]
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=agg.index,
        y=agg.values,
        marker_color=bar_colors
    ))
    fig.update_layout(
        title=dict(text=title, font=dict(size=22, family="Arial", color="black")),
        xaxis_title="Category",
        yaxis_title=value_col,
        font=dict(size=16, family="Arial", color="black"),
        plot_bgcolor="#fafafa",
        height=500,
        margin=dict(l=60, r=40, t=60, b=60),
        showlegend=False
    )
    logo_path = os.path.join(os.path.dirname(__file__), "wcm_logo.png")
    if os.path.exists(logo_path):
        add_logo_to_fig(fig, logo_path)
    return fig

def plot_pareto_scrap_bgrade(df, color_map):
    df = df.copy()
    df["Scrap (m²)"] = pd.to_numeric(df["Scrap (m²)"], errors="coerce").fillna(0)
    df["B-Grade (m²)"] = pd.to_numeric(df["B-Grade (m²)"], errors="coerce").fillna(0)
    df["Total Scrap+B-Grade"] = df["Scrap (m²)"] + df["B-Grade (m²)"]
    agg = df.groupby("Category")["Total Scrap+B-Grade"].sum().sort_values(ascending=False)
    bar_colors = [color_map.get(cat, "#888888") for cat in agg.index]
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=agg.index,
        y=agg.values,
        marker_color=bar_colors
    ))
    fig.update_layout(
        title=dict(text="Pareto: Scrap + B-Grade (m²) by Category", font=dict(size=22, family="Arial", color="black")),
        xaxis_title="Category",
        yaxis_title="Scrap + B-Grade (m²)",
        font=dict(size=16, family="Arial", color="black"),
        plot_bgcolor="#fafafa",
        height=500,
        margin=dict(l=60, r=40, t=60, b=60),
        showlegend=False
    )
    logo_path = os.path.join(os.path.dirname(__file__), "wcm_logo.png")
    if os.path.exists(logo_path):
        add_logo_to_fig(fig, logo_path)
    return fig

def plot_pareto_by_title(df, value_col, title, color_map):
    df = df.copy()
    df = df[df["Title"].notnull()]
    df[value_col] = pd.to_numeric(df[value_col], errors="coerce").fillna(0)
    agg = df.groupby("Title")[value_col].sum().sort_values(ascending=False)
    title_to_cat = df.set_index("Title")["Category"].to_dict()
    bar_colors = [color_map.get(title_to_cat.get(title, ""), "#888888") for title in agg.index]
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=agg.index,
        y=agg.values,
        marker_color=bar_colors,
        text=agg.values,
        textposition="outside",
        textfont=dict(size=22, family="Arial", color="black")
    ))
    fig.update_layout(
        title=dict(text=title, font=dict(size=32, family="Arial", color="black")),
        xaxis_title="Title",
        yaxis_title=value_col,
        font=dict(size=22, family="Arial", color="black"),
        xaxis=dict(
            title_font=dict(size=24, family="Arial", color="black"),
            tickfont=dict(size=20, family="Arial", color="black"),
        ),
        yaxis=dict(
            title_font=dict(size=24, family="Arial", color="black"),
            tickfont=dict(size=20, family="Arial", color="black"),
        ),
        plot_bgcolor="#fafafa",
        height=700,
        margin=dict(l=60, r=40, t=80, b=80),
        showlegend=False
    )
    logo_path = os.path.join(os.path.dirname(__file__), "wcm_logo.png")
    if os.path.exists(logo_path):
        add_logo_to_fig(fig, logo_path)
    return fig

def plot_pareto_scrap_bgrade_by_title(df, color_map):
    df = df.copy()
    df["Scrap (m²)"] = pd.to_numeric(df["Scrap (m²)"], errors="coerce").fillna(0)
    df["B-Grade (m²)"] = pd.to_numeric(df["B-Grade (m²)"], errors="coerce").fillna(0)
    df["Total Scrap+B-Grade"] = df["Scrap (m²)"] + df["B-Grade (m²)"]
    agg = df.groupby("Title")["Total Scrap+B-Grade"].sum().sort_values(ascending=False)
    title_to_cat = df.set_index("Title")["Category"].to_dict()
    bar_colors = [color_map.get(title_to_cat.get(title, ""), "#888888") for title in agg.index]
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=agg.index,
        y=agg.values,
        marker_color=bar_colors,
        text=agg.values,
        textposition="outside",
        textfont=dict(size=22, family="Arial", color="black")
    ))
    # Accept dynamic title
    chart_title = "Pareto: Scrap + B-Grade (m²)"
    if hasattr(df, "_pareto_title"):
        chart_title = df._pareto_title
    fig.update_layout(
        title=dict(text=chart_title, font=dict(size=32, family="Arial", color="black")),
        xaxis_title="Title",
        yaxis_title="Scrap + B-Grade (m²)",
        font=dict(size=22, family="Arial", color="black"),
        xaxis=dict(
            title_font=dict(size=24, family="Arial", color="black"),
            tickfont=dict(size=20, family="Arial", color="black"),
        ),
        yaxis=dict(
            title_font=dict(size=24, family="Arial", color="black"),
            tickfont=dict(size=20, family="Arial", color="black"),
        ),
        plot_bgcolor="#fafafa",
        height=700,
        margin=dict(l=60, r=40, t=80, b=80),
        showlegend=False
    )
    logo_path = os.path.join(os.path.dirname(__file__), "wcm_logo.png")
    if os.path.exists(logo_path):
        add_logo_to_fig(fig, logo_path)
    return fig

def plot_dynamic_pareto_by_title(df, value_col, view_mode, selected_date, color_map):
    filtered_df, dynamic_title = filter_by_view(df, view_mode, selected_date)
    chart_title = f"Pareto: {value_col} - {dynamic_title}"
    return plot_pareto_by_title(filtered_df, value_col, chart_title, color_map)
def filter_by_view(df, view_mode, selected_date):
    df = df.copy()
    from parsing.dates import parse_datetimes
    from datetime import datetime
    import pandas as pd
    start_dt, _ = parse_datetimes(df)
    if view_mode == "Day":
        day_start = datetime.combine(selected_date, datetime.min.time()) + pd.Timedelta(hours=5)
        day_end = day_start + pd.Timedelta(days=1)
        mask = (start_dt >= day_start) & (start_dt < day_end)
        title = f"{selected_date.strftime('%d.%m.%Y')}"
        return df[mask], title
    elif view_mode == "Week":
        week_start = selected_date - pd.Timedelta(days=selected_date.weekday())
        week_start = datetime.combine(week_start, datetime.min.time()) + pd.Timedelta(hours=5)
        week_end = week_start + pd.Timedelta(days=7)
        cw = week_start.isocalendar()[1]
        mask = (start_dt >= week_start) & (start_dt < week_end)
        title = f"CW {cw}"
        return df[mask], title
    else:  # Month
        month_start = datetime(selected_date.year, selected_date.month, 1) + pd.Timedelta(hours=5)
        if selected_date.month == 12:
            next_month = datetime(selected_date.year + 1, 1, 1)
        else:
            next_month = datetime(selected_date.year, selected_date.month + 1, 1)
        month_end = next_month + pd.Timedelta(hours=5)
        mask = (start_dt >= month_start) & (start_dt < month_end)
        title = f"{selected_date.strftime('%m.%Y')}"
        return df[mask], title

def plot_dynamic_pareto_scrap_bgrade_by_title(df, view_mode, selected_date, color_map):
    filtered_df, dynamic_title = filter_by_view(df, view_mode, selected_date)
    filtered_df = filtered_df.copy()
    filtered_df._pareto_title = f"Pareto: Scrap + B-Grade (m²) - {dynamic_title}"
    return plot_pareto_scrap_bgrade_by_title(filtered_df, color_map)
