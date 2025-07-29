import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import os
import pandas as pd
from parsing.dates import parse_datetimes
from utils.colors import get_color
from utils.branding import add_logo_to_fig

def plot_timeline(df, view_mode, selected_date, color_map, show_description=True):
    if df.empty:
        return go.Figure()
    df = df.copy()
    df["Start_dt"], df["End_dt"] = parse_datetimes(df)
    df["Color"] = df["Category"].map(lambda c: get_color(c, color_map))

    # Only keep rows with valid datetimes and positive duration
    df = df[
        df["Start_dt"].notnull() &
        df["End_dt"].notnull() &
        (df["End_dt"] > df["Start_dt"])
    ]

    # Filter by selected date/range using Start_dt
    if view_mode == "Day":
        day_start = datetime.combine(selected_date, datetime.min.time()) + timedelta(hours=5)
        day_end = day_start + timedelta(days=1)
        xaxis_range = [day_start, day_end]
        mask = (df["Start_dt"] >= day_start) & (df["Start_dt"] < day_end)
    elif view_mode == "Week":
        week_start = selected_date - timedelta(days=selected_date.weekday())
        week_start = datetime.combine(week_start, datetime.min.time()) + timedelta(hours=5)
        week_end = week_start + timedelta(days=7)
        xaxis_range = [week_start, week_end]
        mask = (df["Start_dt"] >= week_start) & (df["Start_dt"] < week_end)
    else:  # Month
        month_start = datetime(selected_date.year, selected_date.month, 1) + timedelta(hours=5)
        if selected_date.month == 12:
            next_month = datetime(selected_date.year + 1, 1, 1)
        else:
            next_month = datetime(selected_date.year, selected_date.month + 1, 1)
        month_end = next_month + timedelta(hours=5)
        xaxis_range = [month_start, month_end]
        mask = (df["Start_dt"] >= month_start) & (df["Start_dt"] < month_end)
    df = df[mask]

    if df.empty:
        fig = go.Figure()
        fig.update_layout(
            xaxis=dict(title="Time"),
            yaxis=dict(title="Category"),
            height=600,
            margin=dict(l=80, r=40, t=40, b=40),
            title="Timeline View: (no data for this range)"
        )
        return fig

    # --- Advanced swimlane assignment for monthly view ---
    df = df.sort_values(["Category", "Start_dt", "End_dt"])
    df["SubLane"] = 0
    if view_mode == "Month":
        # Assign swimlanes so that events from the same category on the same day get separate lanes,
        # but events from other days reuse lanes if possible.
        swimlane_map = {}
        for cat in df["Category"].unique():
            cat_df = df[df["Category"] == cat]
            lanes = []
            for idx, row in cat_df.iterrows():
                event_day = row["Start_dt"].date()
                placed = False
                # Try to place in an existing lane if no overlap on that day
                for i, lane in enumerate(lanes):
                    # Check if any event in this lane is on the same day
                    if not any(ev["Start_dt"].date() == event_day for ev in lane):
                        lane.append(row)
                        df.at[idx, "SubLane"] = i
                        placed = True
                        break
                if not placed:
                    lanes.append([row])
                    df.at[idx, "SubLane"] = len(lanes) - 1
            swimlane_map[cat] = len(lanes)
    else:
        # Default: assign swimlanes for overlapping events as before
        for cat in df["Category"].unique():
            cat_df = df[df["Category"] == cat]
            sublanes = []
            for idx, row in cat_df.iterrows():
                placed = False
                for i, lane in enumerate(sublanes):
                    if row["Start_dt"] >= lane[-1]["End_dt"]:
                        lane.append(row)
                        df.at[idx, "SubLane"] = i
                        placed = True
                        break
                if not placed:
                    sublanes.append([row])
                    df.at[idx, "SubLane"] = len(sublanes) - 1

    # Only add SubLane number if there is more than one for this category
    def swimlane_label(row):
        cat = row["Category"]
        max_sublane = df[df["Category"] == cat]["SubLane"].max()
        if max_sublane > 0:
            return f"{cat} {row['SubLane']+1}"
        else:
            return cat
    df["Swimlane"] = df.apply(swimlane_label, axis=1)

    # Prepare custom text for each block (HTML for bold title)
    if show_description:
        df["BlockText"] = (
            "<b style='font-size:22px;display:block;text-align:center'>" + df["Title"].astype(str) + "</b><br>" +
            "<span style='display:block;text-align:left'>Duration: " + df["Duration (min)"].astype(str) + " min<br>" +
            "Scrap + B-Grade: " +
            (
                pd.to_numeric(df["Scrap (m²)"], errors="coerce").fillna(0) +
                pd.to_numeric(df["B-Grade (m²)"], errors="coerce").fillna(0)
            ).astype(int).astype(str) + " m²<br>" +
            "Total Costs: " + df["Cost (€)"].astype(str) + " €</span>"
        )
    else:
        df["BlockText"] = "<b style='font-size:22px;display:block;text-align:center'>" + df["Title"].astype(str) + "</b>"

    fig = px.timeline(
        df,
        x_start="Start_dt",
        x_end="End_dt",
        y="Swimlane",
        color="Category",
        text=None,  # We'll use custom annotations instead of text
        hover_data=["Title", "Description", "Scrap (m²)", "B-Grade (m²)", "Reserved", "Cost (€)"],
        category_orders={"Swimlane": list(df["Swimlane"].unique()), "Category": list(df["Category"].unique())}
    )

    # Get the x-axis range for positioning
    x_min, x_max = xaxis_range

    # Helper to estimate text width in px based on "Scrap + B-Grade: XXXXX m²"
    def estimate_comment_width(row, font_size=18):
        scrap = pd.to_numeric(row["Scrap (m²)"], errors="coerce")
        bgrade = pd.to_numeric(row["B-Grade (m²)"], errors="coerce")
        total = int((scrap if not pd.isnull(scrap) else 0) + (bgrade if not pd.isnull(bgrade) else 0))
        line = f"Scrap + B-Grade: {total} m²"
        return int(len(line) * font_size * 0.5) + 10

    annotation_rects = []
    block_rects = [(row["Start_dt"], row["End_dt"], row["Swimlane"]) for _, row in df.iterrows()]

    for i, row in df.iterrows():
        x0 = row["Start_dt"]
        x1 = row["End_dt"]
        yval = row["Swimlane"]
        x_center = x0 + (x1 - x0) / 2

        min_width_minutes = 30  # allow tighter fit
        block_minutes = (x1 - x0).total_seconds() / 60

        width_px = estimate_comment_width(row)
        width_td = timedelta(hours=width_px / 100)

        # 0. Try inside (at least 120 mins)
        if block_minutes >= 120:
            annotation_overlap = any(
                (x0 < ax1 and x1 > ax0 and yval == ayval)
                for ax0, ax1, ayval in annotation_rects
            )
            if not annotation_overlap:
                fig.add_annotation(
                    x=x_center,
                    y=yval,
                    text=row["BlockText"],
                    showarrow=False,
                    font=dict(size=18, family="Arial", color="black"),
                    align="left",
                    xanchor="center",
                    yanchor="middle",
                    bgcolor="rgba(255,255,255,0.7)",
                    bordercolor="#888",
                    borderwidth=1,
                    borderpad=4,
                    width=None,
                    height=None,
                    opacity=1,
                )
                annotation_rects.append((x0, x1, yval))
                continue

        # 1. Try right (use chart edge, min_width_minutes buffer)
        right_x0 = x1 + timedelta(minutes=10)
        right_x1 = right_x0 + width_td
        right_space = (right_x1 < x_max) and ((x_max - right_x1).total_seconds() / 60 >= min_width_minutes)
        right_overlap = any(
            (right_x0 < bx1 and right_x1 > bx0 and byval == yval)
            for bx0, bx1, byval in block_rects
        ) or any(
            (right_x0 < ax1 and right_x1 > ax0 and yval == ayval)
            for ax0, ax1, ayval in annotation_rects
        )
        if right_space and not right_overlap:
            fig.add_annotation(
                x=right_x0,
                y=yval,
                text=row["BlockText"],
                showarrow=True,
                arrowhead=2,
                arrowcolor="#888",
                arrowwidth=1,
                ax=x1,
                ay=yval,
                axref="x",
                ayref="y",
                font=dict(size=18, family="Arial", color="black"),
                align="left",
                xanchor="left",
                yanchor="middle",
                bgcolor="rgba(255,255,255,0.95)",
                bordercolor="#888",
                borderwidth=1,
                borderpad=4,
                width=width_px,
                opacity=1,
            )
            annotation_rects.append((right_x0, right_x1, yval))
            continue

        # 2. Try left (use chart edge, min_width_minutes buffer)
        left_x1 = x0 - timedelta(minutes=10)
        left_x0 = left_x1 - width_td
        left_space = (left_x0 > x_min) and ((left_x0 - x_min).total_seconds() / 60 >= min_width_minutes)
        left_overlap = any(
            (left_x0 < bx1 and left_x1 > bx0 and byval == yval)
            for bx0, bx1, byval in block_rects
        ) or any(
            (left_x0 < ax1 and left_x1 > ax0 and yval == ayval)
            for ax0, ax1, ayval in annotation_rects
        )
        if left_space and not left_overlap:
            fig.add_annotation(
                x=left_x0,
                y=yval,
                text=row["BlockText"],
                showarrow=True,
                arrowhead=2,
                arrowcolor="#888",
                arrowwidth=1,
                ax=x0,
                ay=yval,
                axref="x",
                ayref="y",
                font=dict(size=18, family="Arial", color="black"),
                align="left",
                xanchor="right",
                yanchor="middle",
                bgcolor="rgba(255,255,255,0.95)",
                bordercolor="#888",
                borderwidth=1,
                borderpad=4,
                width=width_px,
                opacity=1,
            )
            annotation_rects.append((left_x0, left_x1, yval))
            continue

        # 3. Try above (use chart edge, min_width_minutes buffer)
        above_overlap = any(
            (abs(x_center - ax0) < width_td and yval == ayval)
            for ax0, ax1, ayval in annotation_rects
        )
        above_space = True  # always possible in pixel space
        if above_space and not above_overlap:
            fig.add_annotation(
                x=x_center,
                y=yval,
                text=row["BlockText"],
                showarrow=True,
                arrowhead=2,
                arrowcolor="#888",
                arrowwidth=1,
                ax=x_center,
                ayref="pixel",
                ay=-80,
                font=dict(size=18, family="Arial", color="black"),
                align="left",
                xanchor="center",
                yanchor="bottom",
                bgcolor="rgba(255,255,255,0.95)",
                bordercolor="#888",
                borderwidth=1,
                borderpad=4,
                width=width_px,
                opacity=1,
            )
            annotation_rects.append((x_center, x_center, yval))
            continue

        # 4. Try below (use chart edge, min_width_minutes buffer)
        below_overlap = any(
            (abs(x_center - ax0) < width_td and yval == ayval)
            for ax0, ax1, ayval in annotation_rects
        )
        below_space = True  # always possible in pixel space
        fig.add_annotation(
            x=x_center,
            y=yval,
            text=row["BlockText"],
            showarrow=True,
            arrowhead=2,
            arrowcolor="#888",
            arrowwidth=1,
            ax=x_center,
            ayref="pixel",
            ay=80,
            font=dict(size=18, family="Arial", color="black"),
            align="left",
            xanchor="center",
            yanchor="top",
            bgcolor="rgba(255,255,255,0.95)",
            bordercolor="#888",
            borderwidth=1,
            borderpad=4,
            width=width_px,
            opacity=1,
        )
        annotation_rects.append((x_center, x_center, yval))
        # Always place below if all else fails

    # --- Custom x-axis ticks for Month view ---
    if view_mode == "Month":
        # Get all unique days with events
        event_days = sorted(df["Start_dt"].dt.floor("D").unique())
        # Always include the first and last day of the month
        month_start = xaxis_range[0]
        month_end = xaxis_range[1]
        tickvals = [month_start]
        ticktext = [month_start.strftime("%d.%m")]
        for d in event_days:
            if d != month_start and d != month_end:
                tickvals.append(d)
                ticktext.append(d.strftime("%d.%m"))
        tickvals.append(month_end)
        ticktext.append(month_end.strftime("%d.%m"))
        fig.update_xaxes(
            range=xaxis_range,
            tickvals=tickvals,
            ticktext=ticktext,
            tickformat=None,
            dtick=None,
            showgrid=True,
            gridcolor="#e0e0e0",
            gridwidth=1
        )
    elif view_mode == "Day":
        # ...existing code for Day view ticks...
        tickvals = []
        ticktext = []
        current = xaxis_range[0]
        while current <= xaxis_range[1]:
            tickvals.append(current)
            if current.hour == 5 or (current.hour == 0 and current != xaxis_range[0]):
                ticktext.append(current.strftime("%d.%m<br>%H:%M"))
            else:
                ticktext.append(current.strftime("%H:%M"))
            current += timedelta(hours=1)
        fig.update_xaxes(
            range=xaxis_range,
            tickvals=tickvals,
            ticktext=ticktext,
            tickformat=None,
            dtick=3600000,
            showgrid=True,
            gridcolor="#e0e0e0",
            gridwidth=1
        )
        # Add shift indication for the day (same colors as week view)
        shift_colors = ["#C1E5F5", "#F2CFEE", "#D9F2D0"]
        day_start = xaxis_range[0]
        shift1_start = day_start
        shift1_end = day_start + timedelta(hours=8)
        shift2_start = shift1_end
        shift2_end = shift2_start + timedelta(hours=8)
        shift3_start = shift2_end
        shift3_end = day_start + timedelta(days=1)
        fig.add_vrect(
            x0=shift1_start, x1=shift1_end,
            fillcolor=shift_colors[0], opacity=0.18, layer="below", line_width=0
        )
        fig.add_vrect(
            x0=shift2_start, x1=shift2_end,
            fillcolor=shift_colors[1], opacity=0.18, layer="below", line_width=0
        )
        fig.add_vrect(
            x0=shift3_start, x1=shift3_end,
            fillcolor=shift_colors[2], opacity=0.18, layer="below", line_width=0
        )
    else:
        # Week view: only show 05:00 at the start of each day as ticks
        tickvals = []
        ticktext = []
        week_start = xaxis_range[0]
        week_end = xaxis_range[1]
        current = week_start
        while current < week_end:
            tickvals.append(current)
            ticktext.append(current.strftime("%d.%m<br>05:00"))
            current += timedelta(days=1)
        fig.update_xaxes(
            range=xaxis_range,
            tickvals=tickvals,
            ticktext=ticktext,
            tickformat=None,
            dtick=None,
            showgrid=True,
            gridcolor="#e0e0e0",
            gridwidth=1
        )
        # Highlight last 2 days (weekend) with a darker grey rectangle
        sat_start = week_start + timedelta(days=5)
        sun_start = week_start + timedelta(days=6)
        mon_end = week_end
        fig.add_vrect(
            x0=sat_start, x1=sun_start,
            fillcolor="#888888", opacity=0.45, layer="below", line_width=0
        )
        fig.add_vrect(
            x0=sun_start, x1=mon_end,
            fillcolor="#444444", opacity=0.45, layer="below", line_width=0
        )
        # Add shift indication for each day (3 shifts: 05:00-13:00, 13:00-21:00, 21:00-05:00 next day)
        # Use new colors
        shift_colors = ["#C1E5F5", "#F2CFEE", "#D9F2D0"]
        for d in range(7):
            day_start = week_start + timedelta(days=d)
            shift1_start = day_start
            shift1_end = day_start + timedelta(hours=8)
            shift2_start = shift1_end
            shift2_end = shift2_start + timedelta(hours=8)
            shift3_start = shift2_end
            shift3_end = day_start + timedelta(days=1)
            fig.add_vrect(
                x0=shift1_start, x1=shift1_end,
                fillcolor=shift_colors[0], opacity=0.18, layer="below", line_width=0
            )
            fig.add_vrect(
                x0=shift2_start, x1=shift2_end,
                fillcolor=shift_colors[1], opacity=0.18, layer="below", line_width=0
            )
            fig.add_vrect(
                x0=shift3_start, x1=shift3_end,
                fillcolor=shift_colors[2], opacity=0.18, layer="below", line_width=0
            )

    # Add horizontal grid lines for swimlanes
    yvals = list(range(len(df["Swimlane"].unique())))
    fig.update_yaxes(
        autorange="reversed",
        showgrid=True,
        gridcolor="#cccccc",
        gridwidth=2,
        tickfont=dict(size=18, family="Arial", color="black")  # 'bold' removed
    )

    # Format the timeline title as requested
    if view_mode == "Day":
        timeline_title = f"Timeline View: WCM Losses {selected_date.strftime('%d.%m.%Y')}"
    elif view_mode == "Month":
        timeline_title = f"Timeline View: WCM Losses {selected_date.strftime('%m.%Y')}"
    elif view_mode == "Week":
        cw = week_start.isocalendar()[1]
        timeline_title = f"Timeline View: WCM Losses CW {cw}"
    else:
        timeline_title = f"Timeline View: WCM Losses"

    fig.update_layout(
        height=600 + 60 * len(df["Swimlane"].unique()),
        margin=dict(l=80, r=40, t=40, b=40),
        title=dict(
            text=timeline_title,
            font=dict(size=32, family="Arial", color="black")
        ),
        showlegend=False,
        font=dict(size=20, family="Arial", color="black"),
        plot_bgcolor="#fafafa"
    )

    # Add logo to timeline view
    logo_path = os.path.join(os.path.dirname(__file__), "wcm_logo.png")
    if os.path.exists(logo_path):
        add_logo_to_fig(fig, logo_path)

    return fig

def compute_timeline(df, view_mode, selected_date, color_map):
    return plot_timeline(df, view_mode, selected_date, color_map)
