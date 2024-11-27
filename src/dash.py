import pandas as pd
from bokeh.plotting import curdoc
from bokeh.layouts import column, Spacer, gridplot
from bokeh.models import Slider
from scatter import create_scatter_plot, update_plot
from hex_binning import create_hexbin_plot
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


def setup_plots(df_business, df_rolling_reviews, weekdays):
    scatter_plot, scatter_source = create_scatter_plot(df_business, weekdays)
    hexbin_plot, hexbin_source = create_hexbin_plot(df_business)
    historical_plot = create_historical_chart(
        df_rolling_reviews, categories_of_interest
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
    # Load and process data
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
    df_rolling = df_resampled.rolling(365, min_periods=1, win_type="triang").mean()

    # Set up plots and widgets
    scatter_plot, scatter_source, hexbin_plot, historical_plot = setup_plots(
        df_business, df_rolling, weekdays
    )
    widgets = setup_sliders(df_business, scatter_source, weekdays)

    # Layout and add to document
    layout = gridplot([[widgets, scatter_plot, hexbin_plot], [None, historical_plot]])
    curdoc().add_root(layout)


# Run the main function
main()
