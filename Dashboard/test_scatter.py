import pandas as pd
from bokeh.models import ColumnDataSource
from bokeh.plotting import figure, show


def create_test_scatter(df):
    
    
    source = ColumnDataSource(df)
    
    p = figure( tools ="lasso_select, box_select, reset", x_axis_label='stars', y_axis_label='review_count')
    
    p.scatter(x='stars', y='review_count', source=source, selection_color="red")
    
    return p, source

    
    