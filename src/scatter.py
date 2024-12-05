# scatter.py

import time
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

from bokeh.layouts import column
from bokeh.models import (
    Button,
    CDSView,
    Circle,
    CheckboxGroup,
    ColumnDataSource,
    Legend,
    LegendItem,
    Switch,
    BooleanFilter
)

from bokeh.palettes import Colorblind  # For Colorblind palette
from bokeh.plotting import figure
from bokeh.transform import factor_cmap  # For factor-based color mapping
from scipy.stats import gaussian_kde



# Helper functions for data processing

def get_opening_float(time_interval):
    opening_time = time_interval.split("-")
    opening_hour, opening_minute = opening_time[0].split(":")
    opening_time_float = float(opening_hour) + float(opening_minute) / 60.0
    return opening_time_float

def get_closing_float(time_interval):
    opening_time = time_interval.split("-")
    closing_hour, closing_minute = opening_time[1].split(":")
    closing_time_float = float(closing_hour) + float(closing_minute) / 60.0
    return closing_time_float

def get_open_duration_float(time_interval):
    # Split the string into start and end times
    start_time_str, end_time_str = time_interval.split('-')

    # Convert the strings to datetime objects
    start_time = datetime.strptime(start_time_str, "%H:%M")
    end_time = datetime.strptime(end_time_str, "%H:%M")
    
    # Adjust for intervals that cross midnight
    if end_time <= start_time:
        end_time += timedelta(days=1)

    # Calculate the difference in hours and return as a float
    time_difference = end_time - start_time

    hours = time_difference.total_seconds() / 3600
    return abs(hours)

# Function to load and preprocess the data

def load_and_preprocess_data(df):
    df_business = df

    # Define kinds of restaurants we are interested in
    categories_of_interest = ["Burger", "Chinese", "Mexican", "Italian", "Thai", "Other"]

    # Convert column types to string
    df_business = df_business.convert_dtypes()

    # Create new column containing a specific category of interest
    df_business['category_of_interest'] = "Other"
    for item in categories_of_interest:
        df_business.loc[df_business['categories'].str.contains(item, na=False), 'category_of_interest'] = item

    # Define the days of the week for iteration
    weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    rating_groups = ["Rating 1-2", "Rating 2-3", "Rating 3-4", "Rating 4-5"]

    df_business["Rating_Group"] = pd.cut(df_business["stars"], bins=[1,2,3,4,5], labels=rating_groups)

    for day in weekdays:
        # Drop the rows where shops are closed
        df_business = df_business[df_business["hours_" + day] != "Closed"]
        # Create columns for our x-values
        df_business[day + "_Hour_Of_Opening_Float"] = df_business["hours_" + day].apply(get_opening_float)
        # Create columns for our y-values
        df_business[day + "_Open_Duration_Float"] = df_business["hours_" + day].apply(get_open_duration_float)

    return df_business

# Function to create the scatter plot and associated widgets

def create_scatter_components(df_business, source=None):
    # Set up data sources
    if source is None:
        source = ColumnDataSource(df_business)
    else:
        # Update the shared source with df_business data
        source.data = df_business

    scatters_dict = {}
    default_scatter_alpha = 0.7  # Increased alpha for better visibility

    # Define unique colors for the rating groups
    cb = Colorblind[8]
    color_dict = {"Rating 1-2": cb[0],
                  "Rating 2-3": cb[1],
                  "Rating 3-4": cb[3],
                  "Rating 4-5": cb[6]}

    color_list = list(color_dict.values())

    # Define rating groups and weekdays
    rating_groups = ["Rating 1-2", "Rating 2-3", "Rating 3-4", "Rating 4-5"]
    weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    # Create checkbox widgets
    checkboxes_rating_groups = CheckboxGroup(labels=rating_groups, active=[0, 3])
    checkboxes_weekdays = CheckboxGroup(labels=weekdays, active=list(range(len(weekdays))))

    # Create the scatter plot figure with selection tools
    fig_scatter_kd = figure(
        height=600,
        title="Opening Hours and Durations of Restaurants",
        x_axis_label="Opening Hour",
        y_axis_label="Duration",
        x_range=(0, 25),
        y_range=(0, 25),
        tools="wheel_zoom,pan,reset,box_select,lasso_select"
    )

    # Create a BooleanFilter for rating groups
    filter_rating_group = BooleanFilter(booleans=[True] * len(df_business))
    view = CDSView(filter=filter_rating_group)

    # Update functions for checkboxes
    def update_rating_group_filter(attr, old, new):
        selected_labels = [checkboxes_rating_groups.labels[i] for i in checkboxes_rating_groups.active]
        rating_group_column = source.data['Rating_Group']
        booleans = [rg in selected_labels for rg in rating_group_column]
        filter_rating_group.booleans = booleans

    checkboxes_rating_groups.on_change("active", update_rating_group_filter)

    def update_weekdays_visibility(attr, old, new):
        active = checkboxes_weekdays.active
        active_days = [checkboxes_weekdays.labels[i] for i in active]
        for day, scatter_list in scatters_dict.items():
            visible = day in active_days
            for scatter in scatter_list:
                scatter.visible = visible

    checkboxes_weekdays.on_change('active', update_weekdays_visibility)

    for weekday in weekdays:
        scatters_dict[weekday] = []
        scatter = fig_scatter_kd.scatter(
            x=weekday + "_Hour_Of_Opening_Float",
            y=weekday + "_Open_Duration_Float",
            source=source,
            size=6,
            color=factor_cmap("Rating_Group", color_list, rating_groups),
            alpha=default_scatter_alpha,
            view=view,
        )

        # Define the appearance of selected data points
        selected_circle = Circle(
            x=weekday + "_Hour_Of_Opening_Float",
            y=weekday + "_Open_Duration_Float",
            fill_color='firebrick',
            line_color='firebrick',
            radius=0.2,
            fill_alpha=1.0,
            line_alpha=1.0,
        )
        scatter.selection_glyph = selected_circle

        # Define the appearance of non-selected data points
        nonselected_circle = Circle(
            x=weekday + "_Hour_Of_Opening_Float",
            y=weekday + "_Open_Duration_Float",
            fill_color='gray',
            line_color='gray',
            radius=0.1,
            fill_alpha=0.2,
            line_alpha=0.2,
        )
        scatter.nonselection_glyph = nonselected_circle

        scatters_dict[weekday].append(scatter)

    return fig_scatter_kd, checkboxes_rating_groups, checkboxes_weekdays, scatters_dict, source

# Function to create the kernel density plot components

def create_kernel_density_components(df_business, fig_scatter_kd, checkboxes_rating_groups, checkboxes_weekdays, scatters_dict, source):
    # Variables and data sources
    contours_dict = {}
    contours_show = False
    last_press_time = time.time()

    # Define unique colors for the rating groups
    cb = Colorblind[8]
    color_dict = {"Rating 1-2": cb[0],
                  "Rating 2-3": cb[1],
                  "Rating 3-4": cb[3],
                  "Rating 4-5": cb[6]}

    default_selected_rating_groups = ["Rating 1-2", "Rating 4-5"]
    weekdays = checkboxes_weekdays.labels
    rating_groups = checkboxes_rating_groups.labels

    source_weekdays = ColumnDataSource(data={'days': weekdays})
    source_rating_groups = ColumnDataSource(data={'Rating_Groups': default_selected_rating_groups})

    # Helper functions
    def set_scatters_alpha(alpha):
        for scatter_list in scatters_dict.values():
            for scatter in scatter_list:
                scatter.glyph.line_alpha = alpha
                scatter.glyph.fill_alpha = alpha

    def toggle_kd_handler(attr, old, new):
        nonlocal contours_show
        contours_show = new

        if new:
            compute_kernel_density_plots()
            set_scatters_alpha(0.01)
        else:
            remove_contours(fig_scatter_kd)
            set_scatters_alpha(0.1)

    def get_concatenated_x_and_y_from_days(df_source, days):
        if not days:
            return pd.DataFrame({'Concatenated_Hour_Of_Opening_Float': [],
                                 'Concatenated_Open_Duration_Float': []})
        series_acc_x = df_source[days[0] + "_Hour_Of_Opening_Float"]
        series_acc_y = df_source[days[0] + "_Open_Duration_Float"]
        for day in days[1:]:
            series_acc_x = pd.concat([series_acc_x, df_source[day + "_Hour_Of_Opening_Float"]])
            series_acc_y = pd.concat([series_acc_y, df_source[day + "_Open_Duration_Float"]])
        return pd.DataFrame({'Concatenated_Hour_Of_Opening_Float': series_acc_x,
                             'Concatenated_Open_Duration_Float': series_acc_y})

    def kde(x, y, N):
        xmin, xmax = x.min(), x.max()
        ymin, ymax = y.min(), y.max()

        X, Y = np.mgrid[xmin:xmax:N*1j, ymin:ymax:N*1j]
        positions = np.vstack([X.ravel(), Y.ravel()])
        values = np.vstack([x, y])
        kernel = gaussian_kde(values)
        Z = np.reshape(kernel(positions).T, X.shape)

        return X, Y, Z

    def kde_plot(fig, x, y, color):
        x_grid, y_grid, z = kde(x, y, 100)
        levels = np.linspace(np.min(z), np.max(z), 6)
        contour = fig.contour(x_grid, y_grid, z, levels[1:], line_color=color)
        return contour

    def remove_contours(fig):
        nonlocal contours_dict
        for contours in contours_dict.values():
            for c in contours:
                if c in fig.renderers:
                    fig.renderers.remove(c)
        contours_dict = {}

    def compute_kernel_density_plots():
        nonlocal contours_show, contours_dict

        if not contours_show:
            print("Contours are hidden. Hence no contour computation.")
            return

        if contours_dict:
            remove_contours(fig_scatter_kd)

        days_to_include = source_weekdays.data['days']
        rating_groups_to_include = source_rating_groups.data['Rating_Groups']

        if not days_to_include:
            print("No days selected. Aborting contour computation.")
            return

        if not rating_groups_to_include:
            print("No rating groups selected. Aborting contour computation.")
            return

        print("Computing contours...")
        for rating_group in rating_groups_to_include:
            df_filtered = df_business[df_business['Rating_Group'] == rating_group]

            df_concatenated = get_concatenated_x_and_y_from_days(df_filtered, days_to_include)
            x = df_concatenated["Concatenated_Hour_Of_Opening_Float"]
            y = df_concatenated["Concatenated_Open_Duration_Float"]
            if x.empty or y.empty:
                continue
            contour = kde_plot(fig=fig_scatter_kd, x=x, y=y, color=color_dict[rating_group])
            contour.name = "Contour_" + rating_group
            contours_dict.setdefault(rating_group, []).append(contour)
        print("Finished computing contours")

    def check_timeout():
        nonlocal last_press_time
        current_time = time.time()
        if current_time - last_press_time >= 1:
            print("No button pressed in the last 1 seconds: Triggering recompute.")
            compute_kernel_density_plots()

    def delayer(attr, old, new):
        nonlocal last_press_time
        last_press_time = time.time()
        print("Button pressed: resetting timer.")
        from bokeh.io import curdoc
        curdoc().add_timeout_callback(check_timeout, 1000)

    def update_weekdays_callback(attr, old, new):
        active = checkboxes_weekdays.active
        filtered_days = [checkboxes_weekdays.labels[i] for i in active]
        source_weekdays.data = {'days': filtered_days}

    def update_rating_groups_callback(attr, old, new):
        active = checkboxes_rating_groups.active
        filtered_rating_groups = [checkboxes_rating_groups.labels[i] for i in active]
        source_rating_groups.data = {'Rating_Groups': filtered_rating_groups}

    checkboxes_rating_groups.on_change('active', update_rating_groups_callback)
    checkboxes_weekdays.on_change('active', update_weekdays_callback)

    # Delay the computation of contours
    checkboxes_weekdays.on_change("active", delayer)
    checkboxes_rating_groups.on_change("active", delayer)

    # Refresh button
    btn_refresh = Button(label="Refresh", button_type="success")

    def refresh_btn_compute_kernel_density_plots():
        print("Refresh button clicked")
        compute_kernel_density_plots()

    btn_refresh.on_click(refresh_btn_compute_kernel_density_plots)

    # Contour toggle switch
    btn_toggle_kd = Switch(active=False)
    btn_toggle_kd.on_change("active", toggle_kd_handler)

    # Legend
    dummy_glyphs = []
    for rating_group in rating_groups:
        dummy_glyphs.append(fig_scatter_kd.scatter(1, 1, size=10, color=color_dict[rating_group], visible=False))

    legend_items = [
        LegendItem(label=rating_groups[i], renderers=[dummy_glyphs[i]])
        for i in range(len(rating_groups))
    ]
    legend = Legend(items=legend_items)
    fig_scatter_kd.add_layout(legend)

    # Compute the initial kernel density plot
    compute_kernel_density_plots()

    return btn_refresh, btn_toggle_kd

# Function to create the complete dashboard layout

def create_dashboard(df, source=None):
    df_business = load_and_preprocess_data(df)
    fig_scatter_kd, checkboxes_rating_groups, checkboxes_weekdays, scatters_dict, source = create_scatter_components(df_business)
    btn_refresh, btn_toggle_kd = create_kernel_density_components(df_business, fig_scatter_kd, checkboxes_rating_groups, checkboxes_weekdays, scatters_dict, source)
    layout = column(checkboxes_rating_groups, checkboxes_weekdays, btn_refresh, btn_toggle_kd, fig_scatter_kd)
    return layout, source
