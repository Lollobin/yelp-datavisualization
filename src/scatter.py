# scatter.py

import time
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

from bokeh.layouts import column, Spacer, row
from bokeh.models import (
    Button,
    CDSView,
    Circle,
    CheckboxGroup,
    ColumnDataSource,
    Legend,
    LegendItem,
    Div,
    Switch,
    BooleanFilter,
    MultiChoice  # Added for category selection
)

from bokeh.palettes import Colorblind
from bokeh.plotting import figure
from bokeh.transform import factor_cmap
from scipy.stats import gaussian_kde


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
    start_time_str, end_time_str = time_interval.split('-')
    start_time = datetime.strptime(start_time_str, "%H:%M")
    end_time = datetime.strptime(end_time_str, "%H:%M")
    if end_time <= start_time:
        end_time += timedelta(days=1)
    time_difference = end_time - start_time
    hours = time_difference.total_seconds() / 3600
    return abs(hours)


def load_and_preprocess_data(df, categories_of_interest):
    df_business = df.convert_dtypes()

    # Ensure "Other" is also included for consistency
    if "Other" not in categories_of_interest:
        categories_of_interest = categories_of_interest + ["Other"]

    # Category_of_interest already processed in dash.py, but let's ensure labels:
    # (If you trust dash.py's processing, you can skip this step.)
    #df_business['category_of_interest'] = df_business['category_of_interest'].astype(str)

    weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    rating_groups = ["Rating 1-2", "Rating 2-3", "Rating 3-4", "Rating 4-5"]

    df_business["Rating_Group"] = pd.cut(df_business["stars"], bins=[1,2,3,4,5], labels=rating_groups, right=True, include_lowest=True) #changed to right=True, include_lowest=True

    for day in weekdays:
        df_business = df_business[df_business["hours_" + day] != "Closed"]
        df_business[day + "_Hour_Of_Opening_Float"] = df_business["hours_" + day].apply(get_opening_float)
        df_business[day + "_Open_Duration_Float"] = df_business["hours_" + day].apply(get_open_duration_float)

    return df_business, categories_of_interest


def create_scatter_components(df_business, categories_of_interest, source=None, city=None):
    if source is None:
        source = ColumnDataSource(df_business)
    else:
        source.data = df_business

    # Define rating groups, weekdays, etc.
    rating_groups = ["Rating 1-2", "Rating 2-3", "Rating 3-4", "Rating 4-5"]
    weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    # Create your filters
    filter_rating_group = BooleanFilter(booleans=[True] * len(df_business))
    filter_category = BooleanFilter(booleans=[True] * len(df_business))

    # Create the combined filter (initially using both filters as-is)
    combined_booleans = [rg and cat for rg, cat in zip(filter_rating_group.booleans, filter_category.booleans)]
    combined_filter = BooleanFilter(booleans=combined_booleans)

    #print("Rating booleans:", filter_rating_group.booleans)
    #print("Category booleans:", filter_category.booleans)
    #print("Combined booleans:", combined_filter.booleans)


    # Create the category selector
    category_selector = MultiChoice(
        title="Select Categories",
        value=categories_of_interest,
        options=categories_of_interest,
        width=120
    )

    # Create rating group checkbox
    checkboxes_rating_groups = CheckboxGroup(labels=rating_groups, active=[0, 1, 2, 3])
    checkboxes_weekdays = CheckboxGroup(labels=weekdays, active=list(range(len(weekdays))))

    # Create figure
    fig_scatter_kd = figure(
        width=900,
        height=600,
        title=f"Opening Hours and Durations of Restaurants in {city}",
        x_axis_label="Opening Hour",
        y_axis_label="Duration",
        x_range=(0, 25),
        y_range=(0, 25),
        tools="wheel_zoom,pan,reset,box_select,lasso_select"
    )

    # Use the combined filter in the view
    view = CDSView(filter=combined_filter)

    # Function to update the combined filter after rating or category filters change
    def update_combined_filter():
        combined_filter.booleans = [rg and cat for rg, cat in zip(filter_rating_group.booleans, filter_category.booleans)]

    # Callback to update rating group filter
    def update_rating_group_filter(attr, old, new):
        selected_labels = [checkboxes_rating_groups.labels[i] for i in checkboxes_rating_groups.active]
        rating_group_column = source.data['Rating_Group']
        filter_rating_group.booleans = [rg in selected_labels for rg in rating_group_column]
        # After updating rating_group filter, also update combined filter
        update_combined_filter()

    checkboxes_rating_groups.on_change("active", update_rating_group_filter)

    # Callback to update category filter
    def update_category_filter(attr, old, new):
        selected_cats = category_selector.value
        cat_column = source.data['category_of_interest']
        filter_category.booleans = [c in selected_cats for c in cat_column]
        # After updating category filter, also update combined filter
        update_combined_filter()

    category_selector.on_change('value', update_category_filter)

    # Callback to update weekday visibility (unchanged logic)
    def update_weekdays_visibility(attr, old, new):
        active = checkboxes_weekdays.active
        active_days = [checkboxes_weekdays.labels[i] for i in active]
        for day, scatter_list in scatters_dict.items():
            visible = day in active_days
            for scatter in scatter_list:
                scatter.visible = visible

    checkboxes_weekdays.on_change('active', update_weekdays_visibility)

    scatters_dict = {}
    cb = Colorblind[8]
    color_dict = {
        "Rating 1-2": cb[0],
        "Rating 2-3": cb[1],
        "Rating 3-4": cb[3],
        "Rating 4-5": cb[6]
    }
    color_list = list(color_dict.values())

    for weekday in weekdays:
        scatters_dict[weekday] = []
        scatter = fig_scatter_kd.scatter(
            x=weekday + "_Hour_Of_Opening_Float",
            y=weekday + "_Open_Duration_Float",
            source=source,
            size=6,
            color=factor_cmap("Rating_Group", color_list, rating_groups),
            alpha=0.7,
            view=view,
        )

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

    return fig_scatter_kd, checkboxes_rating_groups, checkboxes_weekdays, category_selector, scatters_dict, source



def create_kernel_density_components(df_business, fig_scatter_kd, checkboxes_rating_groups, checkboxes_weekdays, category_selector, scatters_dict, source):
    contours_dict = {}
    contours_show = False
    last_press_time = time.time()

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
        X, Y = np.mgrid[0:24:N*1j, 0:24:N*1j]
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


# original code begins 

    # def compute_kernel_density_plots():
    #     nonlocal contours_show, contours_dict

    #     if not contours_show:
    #         return
        
    #     if not category_selector.value or len(category_selector.value) == 0:
    #         print("Aborting because no category is selected")
    #         return

    #     if contours_dict:
    #         remove_contours(fig_scatter_kd)

    #     days_to_include = source_weekdays.data['days']
    #     rating_groups_to_include = source_rating_groups.data['Rating_Groups']
    #     #categories_to_include = source.data['category_of_interest']

    #     if not days_to_include or not rating_groups_to_include:
    #         return

    #     for rating_group in rating_groups_to_include:
    #         df_filtered = df_business[df_business['Rating_Group'] == rating_group]
    #         df_concatenated = get_concatenated_x_and_y_from_days(df_filtered, days_to_include)
    #         x = df_concatenated["Concatenated_Hour_Of_Opening_Float"]
    #         y = df_concatenated["Concatenated_Open_Duration_Float"]
    #         if x.empty or y.empty:
    #             continue
    #         contour = kde_plot(fig=fig_scatter_kd, x=x, y=y, color=color_dict[rating_group])
    #         contour.name = "Contour_" + rating_group
    #         contours_dict.setdefault(rating_group, []).append(contour)


# original code ends
# 
# # new code begins

    def compute_kernel_density_plots():
        nonlocal contours_show, contours_dict

        if not contours_show:
            return

        selected_categories = category_selector.value
        if not selected_categories or len(selected_categories) == 0:
            print("Aborting because no category is selected")
            return

        if contours_dict:
            remove_contours(fig_scatter_kd)

        days_to_include = source_weekdays.data['days']
        rating_groups_to_include = source_rating_groups.data['Rating_Groups']

        if not days_to_include or not rating_groups_to_include:
            return

        for rating_group in rating_groups_to_include:
            df_filtered = df_business[
                (df_business['Rating_Group'] == rating_group) &
                (df_business['category_of_interest'].isin(selected_categories))
            ]

            if df_filtered.empty:
                print(f"No data available for rating group {rating_group} and selected categories.")
                continue

            df_concatenated = get_concatenated_x_and_y_from_days(df_filtered, days_to_include)

            x = df_concatenated["Concatenated_Hour_Of_Opening_Float"]
            y = df_concatenated["Concatenated_Open_Duration_Float"]

            if x.empty or y.empty:
                print(f"Concatenated data for {rating_group} is empty. Skipping KDE.")
                continue
            contour = kde_plot(fig=fig_scatter_kd, x=x, y=y, color=color_dict[rating_group])
            if contour:
                contour.name = "Contour_" + rating_group
                contours_dict.setdefault(rating_group, []).append(contour)



    # new code ends


    def check_timeout():
        nonlocal last_press_time
        current_time = time.time()
        if current_time - last_press_time >= 1:
            compute_kernel_density_plots()

    def delayer(attr, old, new):
        nonlocal last_press_time
        last_press_time = time.time()
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

    btn_refresh = Button(label="Refresh kernel", button_type="success")

    def refresh_btn_compute_kernel_density_plots():
        compute_kernel_density_plots()

    btn_refresh.on_click(refresh_btn_compute_kernel_density_plots)

    btn_toggle_kd = Switch(active=False)
    btn_toggle_kd.on_change("active", toggle_kd_handler)

    dummy_glyphs = []
    for rating_group in rating_groups:
        dummy_glyphs.append(fig_scatter_kd.scatter(1, 1, size=10, color=color_dict[rating_group], visible=False))

    legend_items = [
        LegendItem(label=rating_groups[i], renderers=[dummy_glyphs[i]])
        for i in range(len(rating_groups))
    ]
    legend = Legend(items=legend_items)
    fig_scatter_kd.add_layout(legend)

    # Initially compute contours if toggle is on (it's off by default)
    compute_kernel_density_plots()

    return btn_refresh, btn_toggle_kd


def create_dashboard(df, source=None, categories_of_interest=None, city=None):
    df_business, categories_of_interest = load_and_preprocess_data(df, categories_of_interest)
    fig_scatter_kd, checkboxes_rating_groups, checkboxes_weekdays, category_selector, scatters_dict, source = create_scatter_components(df_business, categories_of_interest, source, city)
    btn_refresh, btn_toggle_kd = create_kernel_density_components(df_business, fig_scatter_kd, checkboxes_rating_groups, checkboxes_weekdays, category_selector, scatters_dict, source)
   
    label = Div(text="<b>Enable kernel:</b>")
    toggle_layout = row(label, btn_toggle_kd)
    # Add category_selector to the widget layout
    widget_layout = column(
        Spacer(height=50),
        category_selector,
        checkboxes_rating_groups,
        checkboxes_weekdays,
        toggle_layout,
        btn_refresh
    )
    scatter_layout = fig_scatter_kd
    return scatter_layout, widget_layout, source
