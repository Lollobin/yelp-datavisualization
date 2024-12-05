# dash.py

from bokeh.io import curdoc
from scatter import create_dashboard

# Create the dashboard layout
layout = create_dashboard()

# Add the layout to the current document
curdoc().add_root(layout)
