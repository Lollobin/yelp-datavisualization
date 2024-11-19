import pandas as pd
from bokeh.plotting import curdoc
from bokeh.layouts import column, row, Spacer, gridplot
from bokeh.models import Slider
from scatter import create_scatter_plot, update_plot
from hex_binning import create_hexbin_plot
from test_scatter import create_test_scatter

####################################
# Configuration
####################################
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


####################################
# Data Processing Functions
####################################
def load_data(file_path):
    # Import data
    df = pd.read_csv(file_path)

    # Handle NaN values
    return df.dropna(subset=["address"])


def process_categories(df, categories):
    # Create new column containing a specific category of interest
    df["category_of_interest"] = "Other"
    for item in categories:
        df.loc[
            df["categories"].str.contains(item, na=False), "category_of_interest"
        ] = item
    return df


def filter_hours(df, weekdays):
    # Process hours of operation for each day
    for day in weekdays:
        df = df[df["hours_" + day] != "Closed"]
    return df


#########################################################################
## Category Filtering Code
#########################################################################
selected_categories = ["Burger", "Chinese", "Mexican", "Italian", "Thai"]

####################################
# Plot Setup Functions
####################################


def transfer_selected_indices(attr, old, new, source, target):
    selected_indices = source.selected.indices
    target.selected.indices = selected_indices


def setup_plots(df, weekdays):
    scatter_plot, scatter_source = create_scatter_plot(df, weekdays)
    hexbin_plot, hexbin_source = create_hexbin_plot(df)

    scatter_source.selected.on_change(
        "indices",
        lambda attr, old, new: transfer_selected_indices(
            attr, old, new, scatter_source, hexbin_source
        ),
    )
    hexbin_source.selected.on_change(
        "indices",
        lambda attr, old, new: transfer_selected_indices(
            attr, old, new, hexbin_source, scatter_source
        ),
    )

    return scatter_plot, scatter_source, hexbin_plot, hexbin_source


def setup_sliders(df, scatter_source, weekdays):
    # Sliders for selecting number of hours open and hours of opening
    hours_slider = Slider(
        title="Minimum Number of Hours Open", start=0, end=24, value=0, step=0.5
    )
    opening_slider = Slider(
        title="Minimum Hours of Opening", start=0, end=24, value=0, step=0.5
    )

    hours_slider.on_change(
        "value",
        lambda attr, old, new: update_plot(
            attr,
            old,
            new,
            df,
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
            df,
            scatter_source,
            weekdays,
            hours_slider.value,
            opening_slider.value,
        ),
    )

    return column(Spacer(width=50), hours_slider, opening_slider)


####################################
# Main Script Execution
####################################
def main():
    file_path = "cleaned_businessV2.csv"
    # C:/Users/Sadik/Desktop/Data vi proj/datavis-group24/Dashboard/cleaned_businessV2.csv

    # Load and process data
    df_business = load_data(file_path)
    df_business = process_categories(df_business, categories_of_interest)
    df_business = filter_hours(df_business, weekdays)

    # Set up plots and widgets
    scatter_plot, scatter_source, hexbin_plot, hexbin_source = setup_plots(df_business, weekdays)
    widgets = setup_sliders(df_business, scatter_source, weekdays)

    # Layout and add to document
    layout = gridplot([[widgets, scatter_plot, hexbin_plot]])
    curdoc().add_root(layout)


# Run the main function
main()
