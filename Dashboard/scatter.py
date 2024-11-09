import pandas as pd
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource
from bokeh.palettes import Colorblind
from datetime import datetime


def get_opening_float(time_interval):
    opening_time = time_interval.split("-")
    opening_hour, opening_minute = opening_time[0].split(":")
    opening_time_float = float(opening_hour) + float(opening_minute) / 60.0
    return opening_time_float


def get_open_duration_float(time_interval):
    start_time_str, end_time_str = time_interval.split("-")
    start_time = datetime.strptime(start_time_str, "%H:%M")
    end_time = datetime.strptime(end_time_str, "%H:%M")
    time_difference = end_time - start_time
    hours = time_difference.total_seconds() / 3600
    return abs(hours)


def create_scatter_plot(df_business, weekdays):
    # Process hours of operation for each day
    for day in weekdays:
        df_business[day + "_Hour_Of_Opening_Float"] = df_business["hours_" + day].apply(
            get_opening_float
        )
        df_business[day + "_Open_Duration_Float"] = df_business["hours_" + day].apply(
            get_open_duration_float
        )

    # Set up Bokeh plot
    source = ColumnDataSource(data=dict(x=[], y=[], color=[], day=[]))

    plot = figure(
        title="Opening Hours of Businesses",
        x_axis_label="Hours of Opening",
        y_axis_label="Number of Hours Restaurant Remains Open",
        width=800,
        tools="wheel_zoom,pan,reset,box_select,lasso_select",
    )

    colors = Colorblind[len(weekdays)]
    for i, day in enumerate(weekdays):
        filtered_df = df_business[df_business[day + "_Open_Duration_Float"].notna()]
        plot.scatter(
            filtered_df[day + "_Hour_Of_Opening_Float"],
            filtered_df[day + "_Open_Duration_Float"],
            color=colors[i],
            size=7,
            alpha=0.3,
            legend_label=day,
        )

    plot.legend.click_policy = "hide"
    plot.add_layout(plot.legend[0], "right")

    return plot, source


def update_plot(attr, old, new, df_business, source, weekdays, min_hours, min_opening):
    new_data = {"x": [], "y": [], "color": [], "day": []}
    colors = Colorblind[len(weekdays)]
    for i, day in enumerate(weekdays):
        filtered_df = df_business[
            (df_business[day + "_Open_Duration_Float"] >= min_hours)
            & (df_business[day + "_Hour_Of_Opening_Float"] >= min_opening)
        ]
        new_data["x"].extend(filtered_df[day + "_Hour_Of_Opening_Float"].tolist())
        new_data["y"].extend(filtered_df[day + "_Open_Duration_Float"].tolist())
        new_data["color"].extend([colors[i]] * len(filtered_df))
        new_data["day"].extend([day] * len(filtered_df))
    source.data = new_data
