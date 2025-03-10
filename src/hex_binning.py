from bokeh.plotting import figure
from bokeh.models import ColumnDataSource, Circle, ImageURL
from pyproj import Transformer, CRS
import xyzservices.providers as xyz
from bokeh.core.properties import value


def create_hexbin_plot(df):
    # Load data and extract relevant columns
    # df = df[["name", "latitude", "longitude"]].copy()

    # Calculate web mercator coordinates
    in_proj = CRS.from_epsg(4326)  # WGS84
    out_proj = CRS.from_epsg(3857)  # Web Mercator
    transformer = Transformer.from_crs(in_proj, out_proj, always_xy=True)
    df["x"], df["y"] = zip(
        *df.apply(
            lambda row: transformer.transform(row["longitude"], row["latitude"]), axis=1
        )
    )
    min_x, max_x = df["x"].min(), df["x"].max()
    min_y, max_y = df["y"].min(), df["y"].max()

    # Create plot
    source = ColumnDataSource(df)
    p = figure(
        title="Restaurants in Philadelphia",
        x_axis_type="mercator",
        y_axis_type="mercator",
        x_range=(min_x, max_x),
        y_range=(min_y, max_y),
        width=500,
        height=500,
        tools="wheel_zoom,pan,reset,box_select,lasso_select",
    )
    p.add_tile(xyz.CartoDB.Positron, retina=True)
    p.grid.visible = False
    p.axis.visible = False

    p.hexbin(
        df["x"], df["y"], size=500, line_color=None, fill_alpha=0.5, syncable=False
    )
    
    circle_renderer = p.circle(
        x="x",
        y="y",
        source=source,
        radius=75,
        fill_color="blue",
        line_color=None,
        fill_alpha=0.1,
    )

    selected_circle = Circle(
        fill_color="firebrick", line_color=None, fill_alpha=0.8, radius=300
    )

    circle_renderer.selection_glyph = selected_circle

    return p, source
