from random import random

from bokeh.layouts import column
from bokeh.models import Button
from bokeh.palettes import RdYlBu3
from bokeh.plotting import figure, curdoc

# Import data
import pandas as pd
from bokeh.io import output_notebook
df_business = pd.read_csv("../data/cleaned_businessV2.csv")
#output_notebook()

#--------------------------------------------------------------

# Helper functions
from datetime import datetime, timedelta

def get_opening_float(time_interval):
    opening_time = time_interval.split("-")
    opening_hour, opening_minute = opening_time[0].split(":")
    opening_time_float = float(opening_hour) + float(opening_minute) / 60.0
    return opening_time_float

def get_closing_float(time_interval):
    opening_time = time_interval.split("-")
    closing_hour, closing_minute = opening_time[1].split(":")
    closing_time_float = float(closing_hour) + float(closing_minute) / 60.0
    return closing_time_float

def get_open_duration_float(time_interval):
    # Split the string into start and end times
    start_time_str, end_time_str = time_interval.split('-')

    # Convert the strings to datetime objects
    start_time = datetime.strptime(start_time_str, "%H:%M")
    end_time = datetime.strptime(end_time_str, "%H:%M")
    
    # Adjust for intervals that cross midnight
    if end_time <= start_time:
        end_time += timedelta(days=1)

    # Calculate the difference in hours and return as a float
    time_difference = end_time - start_time

    hours = time_difference.total_seconds() / 3600
    return abs(hours)

#--------------------------------------------------------------

# Define kinds of restaurants we are interested in. May need to delete this later
# to allow the user to define this with UI
categories_of_interest = ['Chinese', 'Japanese', 'Italian', 'Polish', 'Scandinavian']

# Convert column types to string
df_business = df_business.convert_dtypes()
#print(f"df_business.dtypes: \n{df_business.dtypes}")

# Create new column containing a specific category of interest. 
# If not in interest, label the column value "Other"
df_business['category_of_interest'] = "Other"
for item in categories_of_interest:
    df_business.loc[df_business['categories'].str.contains(item), 'category_of_interest'] = item

# Define the days of the weeks for iteration
weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
rating_groups = ["Rating 1-2", "Rating 2-3", "Rating 3-4", "Rating 4-5"]

df_business["Rating_Group"] = pd.cut(df_business["stars"], bins=[1,2,3,4,5], labels=rating_groups)

for day in weekdays:
    # Drop the columns where shops are closed
    df_business = df_business[df_business["hours_" + day] != "Closed"]
    # Create columns for our x-values
    df_business[day + "_Hour_Of_Opening_Float"] = df_business["hours_" + day ].apply(get_opening_float)
    # Create columns for our y-values
    df_business[day + "_Open_Duration_Float"] = df_business["hours_" + day].apply(get_open_duration_float)



#--------------------------------------------------------------


# Helper function to concatenate all the "<day>_Hour_Of_Opening_Float" columns into 
# one column called "Concatenated_Hour_Of_Opening_Float" 
# and do the same for "<day>_Open_Duration_Float". Return a df with columns 
# "Concatenated_Hour_Of_Opening_Float", "Concatenated_Open_Duration_Float".

# The idea is that we only want to create a kernel density plot on the background
# of the points that we are seeing on the scatterplot. In other words: we do not wish
# to calculate a kernel density plot based on data points we have filtered away or
# turned off the visibility of.
def get_concatenated_x_and_y_from_days(df_source, days):
    # In order to avoid a warning, we will initialise the 
    # accumulator series to be the column of the first day in days
    series_acc_x = df_source[days[0] + "_Hour_Of_Opening_Float"]
    series_acc_y = df_source[days[0] + "_Open_Duration_Float"]
    # Get all x values
    for i, day in enumerate(days):
        # Skip the first element as we initialised the series_acc_x and series_acc_y to 
        # have the values of the first columns of the days
        if i == 0:
            continue
        series_acc_x = pd.concat([series_acc_x, df_source[day + "_Hour_Of_Opening_Float"]])
        series_acc_y = pd.concat([series_acc_y, df_source[day + "_Open_Duration_Float"]])
    return pd.DataFrame({'Concatenated_Hour_Of_Opening_Float': series_acc_x,
                         'Concatenated_Open_Duration_Float': series_acc_y})


#-------------------------------Kernel Density Plot Using Bokeh-------------------------------

from bokeh.io import output_notebook

import numpy as np
from scipy.stats import gaussian_kde
from bokeh.models import ColumnDataSource, CustomJS, Button, Select, Legend, LegendItem
from bokeh.palettes import Blues9
from bokeh.plotting import figure, show
from bokeh.sampledata.autompg import autompg as df
from bokeh.models import CheckboxGroup, CustomJS
from bokeh.models.filters import CustomJSFilter
from bokeh.models import CDSView
from bokeh.layouts import row
from bokeh.plotting import figure, save, output_file, curdoc
from bokeh.palettes import Colorblind  # For Colorblind palette
import time

contours_dict = {}

# Define colors
cb = Colorblind[8]
chosen_cb_colors = [cb[0], cb[1], cb[3], cb[6]]

def kde(x, y, N):
    xmin, xmax = x.min(), x.max()
    ymin, ymax = y.min(), y.max()

    X, Y = np.mgrid[xmin:xmax:N*1j, ymin:ymax:N*1j]
    positions = np.vstack([X.ravel(), Y.ravel()])
    values = np.vstack([x, y])
    kernel = gaussian_kde(values)
    Z = np.reshape(kernel(positions).T, X.shape)

    return X, Y, Z

def kde_plot(fig, x, y, color_palette):
    x, y, z = kde(x, y, 100)
    levels = np.linspace(np.min(z), np.max(z), 6)
    contour = fig.contour(x, y, z, levels[1:], 
              #fill_color=color_palette, 
              line_color=color_palette)
    return contour

# Set up data sources
source = ColumnDataSource(df_business)
source_weekdays = ColumnDataSource(data={'days': weekdays})
source_rating_groups = ColumnDataSource(data={'Rating_Groups': rating_groups})

# Variable to track the last button press time
last_press_time = time.time()

# Display checkboxes for rating group and weekdays. Let all be checked upon load
checkboxes_rating_groups = CheckboxGroup(labels=rating_groups, active=[0,3])
checkboxes_weekdays = CheckboxGroup(labels=weekdays, active=list(range(0, len(weekdays))))

fig = figure(height=400, x_axis_label="Hour of Opening", y_axis_label="Duration",
            x_range = (0,25), y_range = (0,25),
            background_fill_color="white",
            title="Opening Hours vs Opening Duration Density")



def remove_contours():
    global contours_dict
    global fig
    for key, contours in contours_dict.items():
        for c in contours:
            if c in fig.renderers:
                fig.renderers.remove(c)
    contours_dict = {}

def compute_kernel_density_plots(attr, old, new):
    print("Computing contours")
    # Remove current contours before drawing new
    if contours_dict != {}:
        remove_contours()

    days_to_include = source_weekdays.data['days']
    rating_groups_to_include = source_rating_groups.data['Rating_Groups']
    print("rating_groups_to_include", rating_groups_to_include)
    for i, rating_group in enumerate(rating_groups_to_include):
        df_filtered = df_business[df_business['Rating_Group'] == rating_group]

        df_concatenated_hours_and_durations = get_concatenated_x_and_y_from_days(df_filtered, days_to_include)
        contour = kde_plot(fig=fig, 
                        x = df_concatenated_hours_and_durations["Concatenated_Hour_Of_Opening_Float"], 
                        y = df_concatenated_hours_and_durations["Concatenated_Open_Duration_Float"], 
                        color_palette=chosen_cb_colors[i])
        contour.name = "Contour_"+ rating_group
        contours_dict.setdefault(rating_group, []).append(contour)

    # Wire up the new contours to the checkboxes
    # Make rating group checkboxes update the source upon click.
    # Note: The following code works on the assumption that the order of the rating group checkboxes 
    # ([] Rating 1-2, ...,  [] Rating 4-5) does not change. If we change that order (which 
    # I do not expect we will) then the following JSCallback may break)
    # Second note: We run the .js_on_change in here because we want it to rerun every time we recompute
    # such that the checkboxes get rewired to the new contours
    # checkboxes_rating_groups.js_on_change("active", CustomJS(args=dict(contours_dict=contours_dict, fig=fig), code="""
    #     let active = cb_obj.active;                                                                                                                                        
    #     let keys = Object.keys(contours_dict);    
    #     console.log("----- Toggling rating groups visibility ------ ");                                                                                                        
    #     console.log("active: ", active);
    #     console.log("contours_dict", contours_dict);
    #     console.log("keys.length", keys.length);                                                                                                     
                                                                                                                                                                                                    
    #     for (let i=0; i < keys.length; i++) {
    #         let contour_key = keys[i]; 
    #         console.log("contour_key", contour_key);                                                                                                                                                                                                           
    #         let contour_plot = contours_dict[contour_key][0]; // The value of the dictionary is an array with one element
    #         console.log("contour_plot", contour_plot);                                                                                                                                                                                                           
    #         contour_plot.visible = active.includes(i);
    #         console.log("contour_plot.visible", contour_plot.visible);                                                                                                                                                                                                           
    #     }
    #     //console.log("contour_plot.visible", contour_plot.visible);                                                                                                                                                                                                                                                        
    #     //fig.reset.emit(); // This is what updates the view, such that when a checkbox is pressed, the figure is re-rendered                                                                                                                                                                                                                                                                  
    #     console.log("----- Toggling rating groups visibility end ------ "); 
    # """))
    print("Finished computing contours")


checkboxes_weekdays.js_on_change('active', CustomJS(args=dict(source_weekdays=source_weekdays, weekdays=weekdays, fig=fig), code="""
    let active = cb_obj.active;  // Get the indices of checked boxes
    console.log("active indices: ", active);
                                                    
    // Filter the weekdays based on the active indices
    let filtered_days = active.map(i => weekdays[i]);
    
    // Update the source_weekdays data
    source_weekdays.data = { days: filtered_days };
    source_weekdays.change.emit();  // Notify Bokeh that the data has changed
    fig.reset.emit();                                                
    console.log("source_weekdays.data", source_weekdays.data);
"""))

# Function to delay firing of an event (namely the countor recomputation) for 2 seconds
def check_timeout():
    global last_press_time
    current_time = time.time()
    if current_time - last_press_time >= 1:
        print("No button pressed in the last 1 seconds: Triggering recompute.")
        # Arguments are required in order to compile, but we don't use them
        compute_kernel_density_plots(attr="active", old=[], new=[])

# Button callback to update the last press time
def delayer(attr, old, new):
    global last_press_time
    last_press_time = time.time()
    print("ckdp_attr, old, new,", attr, old, new)
    print("Button pressed: resetting timer.")
    curdoc().add_timeout_callback(check_timeout, 1000)

#checkboxes_weekdays.on_change("active", compute_kernel_density_plots)
checkboxes_weekdays.on_change("active", delayer)
checkboxes_rating_groups.on_change("active", delayer)

# This triggers some js code to update which rating groups we want to compute contours for based
# on which checkboxes are currently checked
checkboxes_rating_groups.js_on_change('active', CustomJS(args=dict(source_rating_groups=source_rating_groups, rating_groups=rating_groups, fig=fig), code="""
    let active = cb_obj.active;  // Get the indices of checked boxes
    console.log(" ----- Updating source_rating_groups -----");
    console.log("active indices: ", active);
                                                    
    // Filter the rating groups based on the active indices
    console.log("Filtering rating groups");
    let filtered_rating_groups = active.map(i => rating_groups[i]);
    
    console.log("filtered_rating_groups", filtered_rating_groups);
                                                         
    // Update the rating_groups data
    console.log("Filtering rating groups");                                   
    source_rating_groups.data = { Rating_Groups: filtered_rating_groups };
                                                         
    console.log("source_rating_groups.data", source_rating_groups.data);                                   
    source_rating_groups.change.emit();  // Notify Bokeh that the data has changed
    fig.reset.emit();                                                
    //console.log("source_rating_groups.data", source_rating_groups.data);
    console.log(" ----- Updating source_rating_groups end -----");
                                                         
"""))

for key, value in contours_dict.items(): print(key, value[0].name, value[0])

fig.grid.level = "overlay"
fig.grid.grid_line_color = "black"
fig.grid.grid_line_alpha = 0.05

# Add the legend as a layout item to the right of the plot.
#p.add_layout(p.legend, 'right')

# Compute the first kernel density plot.
compute_kernel_density_plots(attr="active", old=[], new=[0,1,2,3,4,5,6])

#output_file("kernel-density-plot-toggleable.html")
show(row(fig, checkboxes_rating_groups, checkboxes_weekdays))

#--------------------------------------------------------------

# put the button and plot in a layout and add to the document
curdoc().add_root(column(checkboxes_rating_groups, checkboxes_weekdays, fig))