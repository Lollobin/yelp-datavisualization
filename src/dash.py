from bokeh.io import curdoc 
import pandas as pd 
from bokeh.layouts import column, row, Spacer, gridplot, grid 
from bokeh.models import Slider, Select, ColumnDataSource, Div
from scatter import create_dashboard
from hexbin import create_hexbin_plot
from historical_chart import create_historical_chart


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
        df.loc[df["categories"].str.contains(item, na=False), "category_of_interest"] = item
    return df


def filter_hours(df, weekdays):
    # Process hours of operation for each day
    for day in weekdays:
        df = df[df["hours_" + day] != "Closed"]
    return df

####################################
# City-Specific File Setup
####################################
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


def load_city_data(city=None):
    #Load city-specific business and review data.
    # As a placeholder, we're always loading Philadelphia data. 
    # In a real scenario, use city to load appropriate data files.
    df_business = load_data("../data/cleaned_businessV2.csv")
    df_business = process_categories(df_business, categories_of_interest)
    df_business = filter_hours(df_business, weekdays)

    df_review = pd.read_csv("../data/crosslisted_reviews.csv")
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
    df_historical_reviews = df_resampled.rolling(365, min_periods=1, win_type="triang").mean()

    return df_business, df_historical_reviews


def update_city(attr, old, new):
    selected_city = city_selector.value
    df_business, df_grouped = load_city_data(selected_city)
    # In a full implementation, you'd update your sources and plots here.

# Create city selector widget
city_selector = Select(
    title="Select City",
    value=list(city_files.keys())[0],
    options=list(city_files.keys()),
)
city_selector.on_change("value", update_city)


#data selector to included

######
# code goes here
df_business_data, df_historical_reviews = load_city_data()
######

shared_source = ColumnDataSource(df_business_data)

# Pass categories_of_interest into create_dashboard so it can use them
scatter_layout, widget_layout, shared_source = create_dashboard(df_business_data, shared_source, categories_of_interest)
hexbin_plot = create_hexbin_plot(df_business_data, shared_source)
historical_plot = create_historical_chart(df_historical_reviews, categories_of_interest)

heading = Div(
    text="""
    <div style="display:flex; justify-content:center;">
       <h1 style="font-family: Arial, sans-serif; margin:0; padding:10px; font-size: 36px;">
         Yelp Data Visualization for Restaurants
       </h1>
    </div>
    """,
    height=100,
   # sizing_mode="stretch_width"  
)

row1 = row(
    Spacer(width=40), hexbin_plot, Spacer(width=60), scatter_layout, Spacer(width=100), widget_layout
)

heading_col = column(heading, align="center")

# Ensure the grid also stretches horizontally
layout = grid(
    [
        [heading_col],
        [row1],
        [historical_plot]
    ],
    sizing_mode="scale_height"  # or "scale_width"
)

curdoc().add_root(layout)
