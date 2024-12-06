from bokeh.io import curdoc
import pandas as pd
from bokeh.layouts import column, row, Spacer, grid
from bokeh.models import Slider, Select, ColumnDataSource, Div, Button
from scatter import create_dashboard
from hexbin import create_hexbin_plot
from historical_chart import create_historical_chart

####################################
# Configuration
####################################
categories_of_interest = ["Burger", "Chinese", "Mexican", "Italian", "Thai"]
weekdays = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]

####################################
# Data Processing Functions
####################################
def load_data(file_path):
    df = pd.read_csv(file_path)
    return df.dropna(subset=["address"])

def process_categories(df, categories):
    df["category_of_interest"] = "Other"
    for item in categories:
        df.loc[df["categories"].str.contains(item, na=False), "category_of_interest"] = item
    return df

def filter_hours(df, weekdays):
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

def load_city_data(city):
    paths = city_files[city]
    df_business = load_data(paths["business"])
    df_business = process_categories(df_business, categories_of_interest)
    df_business = filter_hours(df_business, weekdays)

    df_review = pd.read_csv(paths["reviews"])
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

# City selector widget
city_selector = Select(
    title="Select City",
    value=list(city_files.keys())[0],
    options=list(city_files.keys()),
    width=150
)

# Refresh button
btn_refresh = Button(label="Refresh Plots", button_type="success", width=120)

def rebuild_layout(city):
    df_business_data, df_historical_reviews = load_city_data(city)
    shared_source = ColumnDataSource(df_business_data)
    scatter_layout, widget_layout, shared_source = create_dashboard(df_business_data, shared_source, categories_of_interest, city)
    hexbin_plot = create_hexbin_plot(df_business_data, shared_source, city)
    historical_plot = create_historical_chart(df_historical_reviews, categories_of_interest, city)

    heading = Div(
        text="""
        <div style="display:flex; justify-content:center;">
        <h1 style="font-family: Arial, sans-serif; margin:0; padding:10px; font-size: 36px;">
            Yelp Data Visualization for Restaurants
        </h1>
        </div>
        """,
        height=80,
    )

    row1 = row(
        Spacer(width=40), hexbin_plot, Spacer(width=60), scatter_layout, Spacer(width=100), widget_layout
    )

    heading_col = column(heading, align="center")

    # city_selector and refresh button above heading for convenience
    control_row = row(Spacer(width=40), city_selector, Spacer(width=1800), btn_refresh )

    layout = grid(
        [
            [heading_col],
            [control_row],
            [row1],
            [historical_plot]
        ],
        sizing_mode="scale_height"
    )
    return layout

def update_city(attr, old, new):
    selected_city = city_selector.value
    layout_new = rebuild_layout(selected_city)
    curdoc().clear()
    curdoc().add_root(layout_new)

def refresh_layout():
    selected_city = city_selector.value
    layout_new = rebuild_layout(selected_city)
    curdoc().clear()
    curdoc().add_root(layout_new)

city_selector.on_change("value", update_city)
btn_refresh.on_click(refresh_layout)

# Initial setup
default_city = city_selector.value
initial_layout = rebuild_layout(default_city)
curdoc().add_root(initial_layout)
