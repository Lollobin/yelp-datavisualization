import pandas as pd
from bokeh.plotting import curdoc
from bokeh.layouts import column, Spacer, gridplot
from bokeh.models import Slider
from scatter import create_scatter_plot, update_plot
from hex_binning import create_hexbin_plot
from historical_chart import create_historical_chart
from bokeh.models import Select

####################################
# City-Specific File Setup
####################################
# Dictionary mapping cities to their business and reviews files
city_files = {
    "Philadelphia": {
        "business": "../data/cleaned_businessV2.csv",
        "reviews": "../data/crosslisted_reviews.csv",
    },
    "New York": {
        "business": "../data/cleaned_new_york.csv",
        "reviews": "../data/crosslisted_reviews_new_york.csv",
    },
    "Los Angeles": {
        "business": "../data/cleaned_los_angeles.csv",
        "reviews": "../data/crosslisted_reviews_los_angeles.csv",
    },
    # Add more cities as needed
}

def load_city_data(city):
    """Load city-specific business and review data."""
    paths = city_files[city]

    # Load business data
    df_business = load_data(paths["business"])
    df_business = process_categories(df_business, categories_of_interest)
    df_business = filter_hours(df_business, weekdays)

    # Load reviews data specific to the city
    df_review = pd.read_csv(paths["reviews"])
    df_review.rename(columns={"stars": "review_stars"}, inplace=True)
    df_joined = pd.merge(df_business, df_review, on="business_id", how="inner")
    df_joined = df_joined.convert_dtypes()
    df_joined = process_categories(df_joined, categories_of_interest)
    df_joined["Year"] = df_joined["date"].apply(lambda x: x.split("-")[0])
    df_grouped = df_joined.groupby(["category_of_interest", "Year"])[
        "review_stars"
    ].mean()

    return df_business, df_grouped

def update_city(attr, old, new):
    """Callback to update plots when a city is selected."""
    selected_city = city_selector.value
    df_business, df_grouped = load_city_data(selected_city)

    # Update plots
    scatter_plot, scatter_source, hexbin_plot, historical_plot = setup_plots(
        df_business, df_grouped, weekdays
    )
    layout.children[1] = gridplot([[widgets, scatter_plot, hexbin_plot], [None, historical_plot]])

# Create city selector widget
city_selector = Select(
    title="Select City",
    value=list(city_files.keys())[0],
    options=list(city_files.keys()),
)
city_selector.on_change("value", update_city)


####################################
# Configuration
####################################
categories_of_interest = ["Burger", "Chinese", "Mexican", "Italian", "Thai"]
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


####################################
# Plot Setup Functions
####################################


def transfer_selected_indices(attr, old, new, source, target):
    selected_indices = source.selected.indices
    target.selected.indices = selected_indices


def setup_plots(df_business, df_grouped_reviews, weekdays):
    scatter_plot, scatter_source = create_scatter_plot(df_business, weekdays)
    hexbin_plot, hexbin_source = create_hexbin_plot(df_business)
    historical_plot = create_historical_chart(
        df_grouped_reviews, categories_of_interest
    )

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

    return scatter_plot, scatter_source, hexbin_plot, historical_plot


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
    # Initial setup: load data for the default selected city
    selected_city = city_selector.value
    df_business, df_grouped = load_city_data(selected_city)

    # Set up plots and widgets
    scatter_plot, scatter_source, hexbin_plot, historical_plot = setup_plots(
        df_business, df_grouped, weekdays
    )
    widgets = setup_sliders(df_business, scatter_source, weekdays)

    # Create the layout with the city selector and plots
    global layout
    layout = column(
        city_selector,  # Add the city selector at the top
        gridplot(
            [
                [widgets, scatter_plot, hexbin_plot],  # Widgets and plots in the first row
                [None, historical_plot],  # Historical chart in the second row
            ]
        ),
    )

    # Add the layout to the current Bokeh document
    curdoc().add_root(layout)


# Run the main function
main()
