import pandas as pd
from bokeh.plotting import curdoc
from bokeh.layouts import column, row, Spacer, gridplot
from bokeh.models import Slider, MultiChoice, Button, CheckboxGroup, ColumnDataSource, Div
from scatter import create_scatter_plot, get_open_duration_float, get_opening_float
from hex_binning import create_hexbin_plot
from historical_chart import create_historical_chart

####################################
# Configuration
####################################
categories_of_interest = ["Burger", "Chinese", "Mexican", "Italian", "Thai", "Other"]
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
    return df

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
    scatter_plot, scatter_source, scatter_renderers = create_scatter_plot(df_business, weekdays)
    hexbin_plot, hexbin_source = create_hexbin_plot(df_business)
    historical_plot, historical_source = create_historical_chart(
        df_grouped_reviews, categories_of_interest
    )

    """ scatter_source.selected.on_change(
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
    ) """

    return scatter_plot, scatter_source, scatter_renderers, hexbin_plot, hexbin_source, historical_plot, historical_source

####################################
# Main Script Execution
####################################
def main():
    # Load and process data
    df_business = load_data("../data/cleaned_businessV2.csv")
    df_business = process_categories(df_business, categories_of_interest)
    df_business = filter_hours(df_business, weekdays)

    df_review = load_data("../data/crosslisted_reviews.csv")
    df_review.rename(columns={"stars": "review_stars"}, inplace=True)
    df_joined = pd.merge(df_business, df_review, on="business_id", how="inner")
    df_joined = df_joined.convert_dtypes()
    df_joined = process_categories(df_joined, categories_of_interest)
    df_joined["Year"] = df_joined["date"].apply(lambda x: x.split("-")[0])
    df_grouped = df_joined.groupby(["category_of_interest", "Year"], as_index=False)["review_stars"].mean()


    # Set up plots and widgets
    scatter_plot, scatter_source, scatter_renderers, hexbin_plot, hexbin_source, historical_plot, historical_source= setup_plots(
        df_business, df_grouped, weekdays
    )

    initial_count = len(scatter_source.data['index'])
    count_div = Div(text=f"<b>Number of Restaurants Displayed: {initial_count}</b>", styles={'font-size': '16px', 'color': 'blue'})


    # MultiChoice for selecting categories
    category_multichoice = MultiChoice(
        title="Select Restaurant Categories",
        value=categories_of_interest,
        options=categories_of_interest,
    )

    # CheckboxGroup for selecting days of the week
    day_selector = CheckboxGroup(
        #title = "Select Days",
        labels=weekdays,
        active=list(range(len(weekdays))),
    )

    # Slider for selecting ratings
    rating_slider = Slider(title="Minimum Rating", start=1, end=5, value=3, step=.5)

    # Reset button
    reset_button = Button(label="Reset", button_type="success")

    # Update function for widgets
    def update_filters():
        selected_categories = category_multichoice.value
        selected_days = [weekdays[i] for i in day_selector.active]
        min_rating = rating_slider.value

        filtered_df = df_business[
            df_business["category_of_interest"].isin(selected_categories)
        ]
        filtered_df = filtered_df[filtered_df["stars"] >= min_rating]

        #filtered_df = filtered_df.copy()

        # Recompute the columns required for plotting
        """ for day in weekdays:
            filtered_df[day + "_Hour_Of_Opening_Float"] = filtered_df["hours_" + day].apply(
            get_opening_float
        )
            filtered_df[day + "_Open_Duration_Float"] = filtered_df["hours_" + day].apply(
            get_open_duration_float
        ) """

        # Filter by selected days
        """ for day in weekdays:
            if day not in selected_days:
                filtered_df = filtered_df[filtered_df["hours_" + day] == "Closed"] """

        for i, day in enumerate(weekdays):
            if day in selected_days:
                scatter_renderers[i].visible = True
            else:
                scatter_renderers[i].visible = False

        scatter_source.data = ColumnDataSource.from_df(filtered_df)
        #hexbin_source.data = ColumnDataSource.from_df(filtered_df)
        # Update historical chart data
        filtered_grouped = df_grouped[df_grouped["category_of_interest"].isin(selected_categories)]
        historical_source.data = ColumnDataSource.from_df(filtered_grouped)
        count = len(filtered_df)
        count_div.text = f"<b>Number of Restaurants Displayed: {count}</b>"

    # Link the widgets to the update function
    category_multichoice.on_change("value", lambda attr, old, new: update_filters())
    day_selector.on_change("active", lambda attr, old, new: update_filters())
    rating_slider.on_change("value", lambda attr, old, new: update_filters())

    # Reset button callback
    def reset_filters():
        category_multichoice.value = categories_of_interest
        day_selector.active = list(range(len(weekdays)))
        rating_slider.value = 3
        update_filters()


    reset_button.on_click(reset_filters)

    # Layout and add to document
    controls = column(category_multichoice, day_selector, rating_slider, reset_button, count_div)
    layout = gridplot([[hexbin_plot, scatter_plot], [ historical_plot, controls]])

    curdoc().add_root(layout)
    curdoc().title = "Impact of opening hour on restaurant ratings"

# Run the main function
main()
