import pandas as pd
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource, Range1d
from bokeh.palettes import Colorblind
from datetime import datetime, timedelta


def get_opening_float(time_interval):
    opening_time = time_interval.split("-")
    opening_hour, opening_minute = opening_time[0].split(":")
    opening_time_float = float(opening_hour) + float(opening_minute) / 60.0
    return opening_time_float


def get_open_duration_float(time_interval):
    start_time_str, end_time_str = time_interval.split("-")
    start_time = datetime.strptime(start_time_str, "%H:%M")
    end_time = datetime.strptime(end_time_str, "%H:%M")
    if end_time <= start_time:
        end_time += timedelta(days=1)

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
    #source = ColumnDataSource(data=dict(x=[], y=[], color=[], day=[]))
    source = ColumnDataSource(df_business)

    plot = figure(
        title="Opening Hours of Businesses",
        x_axis_label="Opening Duration",
        y_axis_label="Number of Hours Restaurant Remains Open",
        width=800,
       
    )

    colors = Colorblind[len(weekdays)]
    for i, day in enumerate(weekdays):
        #filtered_df = df_business[df_business[day + "_Open_Duration_Float"].notna()]
        plot.scatter(
            x=day + "_Hour_Of_Opening_Float",
            y=day + "_Open_Duration_Float",
            source=source,
            color=colors[i],
            size=7,
            alpha=0.3,
            selection_color="red",          
        )

    # plot.legend.click_policy = "hide"
    # plot.add_layout(plot.legend[0], "right")
    plot.x_range = Range1d(0, 24)
    plot.y_range = Range1d(0, 24)
    return plot, source



