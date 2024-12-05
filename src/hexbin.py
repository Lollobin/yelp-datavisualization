# hexbin.py

from bokeh.plotting import figure
from bokeh.models import ColumnDataSource, Circle
from pyproj import Transformer, CRS
import xyzservices.providers as xyz

def create_hexbin_plot(df, source):
    # Calculate web mercator coordinates
    in_proj = CRS.from_epsg(4326)  # WGS84
    out_proj = CRS.from_epsg(3857)  # Web Mercator
    transformer = Transformer.from_crs(in_proj, out_proj, always_xy=True)
    df["x"], df["y"] = zip(
        *df.apply(
            lambda row: transformer.transform(row["longitude"], row["latitude"]), axis=1
        )
    )
    # Update the shared source with the new 'x' and 'y' coordinates
    source.data.update(df)

    min_x, max_x = df["x"].min(), df["x"].max()
    min_y, max_y = df["y"].min(), df["y"].max()

    # Create plot
    p = figure(
        title="Restaurants in Philadelphia",
        x_axis_type="mercator",
        y_axis_type="mercator",
        x_range=(min_x, max_x),
        y_range=(min_y, max_y),
        width=900,
        height=600,
        tools="wheel_zoom,pan,reset,box_select,lasso_select",
    )
    p.add_tile(xyz.CartoDB.Positron, retina=True)
    p.grid.visible = False
    p.axis.visible = False

    # Add hexbin aggregation as background
    # Unpack the tuple returned by hexbin
    hex_renderer, bins = p.hexbin(
        df["x"], df["y"], size=500, line_color=None, fill_alpha=0.5, syncable=False
    )

    # Disable interactions on hexagons
    hex_renderer.nonselection_glyph = None
    hex_renderer.hover_glyph = None
    hex_renderer.muted_glyph = None
    hex_renderer.selection_glyph = None

    # Plot circles using the shared source after hexbin, so they are on top
    circle_renderer = p.circle(
        x="x",
        y="y",
        source=source,
        radius=100,  # Adjusted radius for better visibility
        fill_color="blue",
        line_color=None,
        fill_alpha=0.5,  # Adjusted fill_alpha for better visibility
    )

    selected_circle = Circle(
        fill_color="firebrick", line_color=None, fill_alpha=0.8, radius=200  # Adjusted radius
    )

    circle_renderer.selection_glyph = selected_circle

    return p
