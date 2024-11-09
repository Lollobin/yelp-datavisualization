import pandas as pd
from bokeh.plotting import curdoc
from bokeh.layouts import column, row, Spacer, gridplot
from bokeh.models import Slider
from scatter import create_scatter_plot, update_plot
from hex_binning import create_hexbin_plot
from test_scatter import create_test_scatter


# Import data
df_business = pd.read_csv("cleaned_businessV2.csv")

# Handle NaN values
df_business = df_business.dropna(subset=["address"])

# Define categories of interest and days of the week
categories_of_interest = ["Chinese", "Japanese", "Italian", "Polish", "Scandinavian"]
weekdays = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]

# Create new column containing a specific category of interest
df_business = df_business.convert_dtypes()
df_business["category_of_interest"] = "Other"
for item in categories_of_interest:
    df_business.loc[
        df_business["categories"].str.contains(item, na=False), "category_of_interest"
    ] = item

# Process hours of operation for each day
for day in weekdays:
    df_business = df_business[df_business["hours_" + day] != "Closed"]

# Set up Bokeh plots
scatter_plot, scatter_source = create_scatter_plot(df_business, weekdays)
hexbin_plot, hexbin_source = create_hexbin_plot(df_business)
test_scatter_plot, test_scatter_source = create_test_scatter(df_business)

# Sliders for selecting number of hours open and hours of opening
hours_slider = Slider(
    title="Minimum Number of Hours Open", start=0, end=24, value=0, step=0.5
)
opening_slider = Slider(
    title="Minimum Hours of Opening", start=0, end=24, value=0, step=0.5
)

# Initial plot update
#update_plot(
#    None,
#    None,
#    None,
#    df_business,
#    scatter_source,
#    weekdays,
#    hours_slider.value,
#    opening_slider.value,
#)

# Add interaction
hours_slider.on_change(
    "value",
    lambda attr, old, new: update_plot(
        attr,
        old,
        new,
        df_business,
        scatter_source,
        weekdays,
        hours_slider.value,
        opening_slider.value,
    ),
)
opening_slider.on_change(
    "value",
    lambda attr, old, new: update_plot(
        attr,
        old,
        new,
        df_business,
        scatter_source,
        weekdays,
        hours_slider.value,
        opening_slider.value,
    ),
)


# Define callback functions for linking and brushing
def select_on_map(attr, old, new):
    selected_indices = hexbin_source.selected.indices
    scatter_source.selected.indices = selected_indices


def select_on_scatter(attr, old, new):
    selected_indices = scatter_source.selected.indices
    hexbin_source.selected.indices = selected_indices

scatter_source.selected.on_change("indices", select_on_scatter)
hexbin_source.selected.on_change("indices", select_on_map)

# Layout and add to document
spacer = Spacer(width=50)
widgets = column(spacer, hours_slider, opening_slider)
layout = gridplot([[widgets, hexbin_plot, scatter_plot]])

curdoc().add_root(layout)
