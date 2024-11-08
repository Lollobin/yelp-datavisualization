import pandas as pd
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource, CustomJS
from bokeh.transform import linear_cmap
from bokeh.util.hex import hexbin
from pyproj import Transformer, CRS
import xyzservices.providers as xyz

def create_hexbin_plot(df):
    # Load data and extract relevant columns and sample
    df = df[["name", "latitude", "longitude"]].copy()

    # Calculate web mercator coordinates
    in_proj = CRS.from_epsg(4326)   # WGS84
    out_proj = CRS.from_epsg(3857)  # Web Mercator
    transformer = Transformer.from_crs(in_proj, out_proj, always_xy=True)
    
    def latlon_to_web_mercator(lat, lon):
        x, y = transformer.transform(lon, lat)
        return x, y
    
    df['x'], df['y'] = zip(*df.apply(lambda x: latlon_to_web_mercator(x.latitude, x.longitude), axis=1))
    max_x = df['x'].max()
    min_x = df['x'].min()
    max_y = df['y'].max()
    min_y = df['y'].min()

    # Create plot
    source = ColumnDataSource(df)
    p = figure(title="Philadelphia Restaurants",
               x_axis_type="mercator", y_axis_type="mercator",
               x_range=(min_x, max_x), y_range=(min_y, max_y),
               width=800, height=600,
               tools="wheel_zoom,pan,reset,box_select,lasso_select")
    p.add_tile(xyz.CartoDB.Positron)
    p.grid.visible = False

    bins = hexbin(df['x'], df['y'], size=500)
    p.hex_tile(q="q", r="r", source=bins,
               size=500, line_color=None, fill_alpha=0.5,
               fill_color=linear_cmap('counts', 'Viridis256', 0, max(bins.counts)))

    p.scatter(x='x', y='y', source=source, size=3, fill_color='black', fill_alpha=0.1, line_color=None)

    source.selected.js_on_change('indices', CustomJS(args=dict(source=source), code="""
        const indices = cb_obj.indices;
        console.log('Number of selected points:', indices.length);
    """))

    return p
