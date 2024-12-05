from bokeh.io import curdoc
import pandas as pd
from bokeh.layouts import column, row, Spacer, gridplot
from bokeh.models import Slider
from bokeh.models import Select
from bokeh.models import ColumnDataSource
from scatter import create_dashboard
from hexbin import create_hexbin_plot


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
# City-Specific File Setup
####################################
# Dictionary mapping cities to their business and reviews files
city_files = {
    "Philadelphia": {
        "business": "../data/cleaned_businessV2.csv",
        "reviews": "../data/crosslisted_reviews.csv",
    },
    "Tucson": {
        "business": "../data/cleaned_business_Tucson.csv",
        "reviews": "../data/crosslisted_reviews_Tucson.csv",
    },
    "Tampa": {
        "business": "../data/cleaned_business_Tampa.csv",
        "reviews": "../data/crosslisted_reviews_Tampa.csv",
    },
}


def load_city_data(): #make sure to include a city parameter
    #Load city-specific business and review data.
    #paths = city_files[city]

    # Load business data
    df_business = load_data("../data/cleaned_businessV2.csv")
    df_business = process_categories(df_business, categories_of_interest)
    df_business = filter_hours(df_business, weekdays)

    # Load reviews data specific to the city
    df_review = pd.read_csv("../data/crosslisted_reviews.csv") #needs to be changed
    df_review.rename(columns={"stars": "review_stars"}, inplace=True)
    df_joined = pd.merge(df_business, df_review, on="business_id", how="inner")
    df_joined = df_joined.convert_dtypes()
    df_joined = process_categories(df_joined, categories_of_interest)

    # Process data for historical chart
    df_joined = df_joined[["review_stars", "date", "category_of_interest"]]
    df_joined["date"] = pd.to_datetime(df_joined["date"])
    df_joined = df_joined.sort_values(by="date")
    df_pivot = df_joined.pivot_table(
        index="date",
        columns="category_of_interest",
        values="review_stars",
        aggfunc="mean",
    )
    df_resampled = df_pivot.resample("D").mean()
    df_historical_reviews = df_resampled.rolling(
        365, min_periods=1, win_type="triang"
    ).mean()

    return df_business, df_historical_reviews


def update_city(attr, old, new):
    #Callback to update plots when a city is selected.
    selected_city = city_selector.value
    df_business, df_grouped = load_city_data(selected_city)

# Create city selector widget
city_selector = Select(
    title="Select City",
    value=list(city_files.keys())[0],
    options=list(city_files.keys()),
)
city_selector.on_change("value", update_city)


df_business_data, df_historical_reviews = load_city_data()

shared_source = ColumnDataSource(df_business_data)

# Create the dashboard layout and pass the shared source
scatter_layout, shared_source = create_dashboard(df_business_data, shared_source)
hexbin_plot = create_hexbin_plot(df_business_data, shared_source)

""" # Function to synchronize selections
def transfer_selected_indices(attr, old, new, source, target): 
    target.selected.indices = source.selected.indices

# Set up on_change callbacks to synchronize selections
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
 """
# Create the dashboard layout as before
layout = row(scatter_layout, hexbin_plot)

# Add the layout to the current document
curdoc().add_root(layout)
