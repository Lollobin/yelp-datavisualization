from bokeh.plotting import figure
from bokeh.palettes import Colorblind


def create_historical_chart(df, categories_of_interest):

    df = df[df.index.year > 2008]

    # create a new plot with a title and axis labels
    p = figure(
        title="Average Rating Throughout the Years by Category",
        x_axis_label="Year",
        y_axis_label="Average Rating",
        x_axis_type="datetime",
    )

    # Get a list of color-blind friendly colors of length = len(categories_of_interest)
    colors = Colorblind[len(categories_of_interest)]

    # Make a line for each category
    for i, category in enumerate(categories_of_interest):
        if category in df.columns:
            p.line(
                df.index,
                df[category],
                legend_label=category,
                color=colors[i],
                line_width=2,
            )

    # Move legend outside the plot
    p.add_layout(p.legend[0], "right")

    # Hide line when clicked on its legend item
    p.legend.click_policy = "hide"

    return p
