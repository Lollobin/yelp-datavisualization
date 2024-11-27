from bokeh.plotting import figure
from bokeh.models import ColumnDataSource
from bokeh.palettes import Colorblind

def create_historical_chart(df, categories_of_interest):
    # create a new plot with a title and axis labels
    p = figure(
        title="Average Rating Throughout the Years by Category",
        x_axis_label="Year",
        y_axis_label="Average Rating",
        width=800,
    )

    # Create ColumnDataSource for data
    source = ColumnDataSource(df)

    # Get a list of color-blind friendly colors of length = len(categories_of_interest)
    colors = Colorblind[len(categories_of_interest)]

    # Make a line for each category
    for i, category in enumerate(categories_of_interest):
        filtered_df = df[df["category_of_interest"] == category]
        p.line(
            x="Year",
            y="review_stars",
            source=ColumnDataSource(filtered_df.reset_index()),
            line_width=2,
            color=colors[i],
        )

    return p, source
