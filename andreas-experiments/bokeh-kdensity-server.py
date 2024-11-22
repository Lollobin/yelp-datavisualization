# Run command `python -m bokeh serve --show .\bokeh-kdensity-server.py` in order to run the server.
# If that doesn't work, try `bokeh serve --show .\bokeh-kdensity-server.py`.

import time
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from bokeh.layouts import column
from bokeh.models import (
    CheckboxGroup,
    ColumnDataSource,
    CustomJS,
    Legend,
    LegendItem,
    Button
)
from bokeh.palettes import Colorblind  # For Colorblind palette
from bokeh.plotting import curdoc, figure
from scipy.stats import gaussian_kde

df_business = pd.read_csv("../data/cleaned_businessV2.csv")

#--------------------------------------------------------------

# Helper functions

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

#---------------------------- Aggregate and Clean Data ----------------------------------

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


#-------------------------------Kernel Density Plot Using Bokeh-------------------------------

# --- Variables --- 

# Define a dictionary to store and access contour plots
contours_dict = {}

# Define unique colors for the rating group
cb = Colorblind[8]
color_dict = {"Rating 1-2" : cb[0], 
              "Rating 2-3" : cb[1],
              "Rating 3-4" : cb[3],
              "Rating 4-5" : cb[6],}

default_selected_rating_groups = ["Rating 1-2", "Rating 4-5"]

# Set up data sources
source = ColumnDataSource(df_business)
source_weekdays = ColumnDataSource(data={'days': weekdays})
source_rating_groups = ColumnDataSource(data={'Rating_Groups': default_selected_rating_groups})

# Variable to track the last button press time. We want a little delay from we press a checkbox until
# we see something happen. Otherwise we will compute contours for every little change to the checkboxes
# which is not necessarily desired and is also computationally demanding and time consuming. 
# Implementing this delay will decrease overhead by waiting until the user is done pressing buttons and
# THEN recompute the kernel density plot. 
last_press_time = time.time()

# Display checkboxes for rating group and weekdays. Upon load, the lowest and highest
# rating group are checked as well as all weekdays.
checkboxes_rating_groups = CheckboxGroup(labels=rating_groups, active=[0,3])
checkboxes_weekdays = CheckboxGroup(labels=weekdays, active=list(range(0, len(weekdays))))
btn_refresh = Button(label="Refresh", button_type="success")

# Create the kernel density plot figure
fig = figure(height=400, x_axis_label="Hour of Opening", y_axis_label="Duration",
            x_range = (0,25), y_range = (0,25),
            background_fill_color="white",
            title="Opening Hours vs Opening Duration Density")

# --- Functions --- 

# Helper function to concatenate all the "<day>_Hour_Of_Opening_Float" columns into 
# one column called "Concatenated_Hour_Of_Opening_Float" 
# and do the same for "<day>_Open_Duration_Float". Return a df with columns 
# "Concatenated_Hour_Of_Opening_Float", "Concatenated_Open_Duration_Float".

# The idea is that we only want to create a kernel density plot on the background
# of the points that we are seeing on the scatterplot. In other words: we do not wish
# to calculate a kernel density plot based on data points we have filtered away or
# turned off the visibility of.
def get_concatenated_x_and_y_from_days(df_source, days):
    # Bail out fast if no days are selected
    if days == []:
        return pd.DataFrame({'Concatenated_Hour_Of_Opening_Float': [],
                             'Concatenated_Open_Duration_Float': []})
    # In order to avoid a warning, we will initialize the 
    # accumulator Series to be the column of the first day in days.
    # Otherwise we will get a warning saying that concatening with an empty
    # Series object is bad and is deprecated behavior
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

# Test to see that above function works as intended. Not implemented in our vis.
def test_get_concatenated_x_and_y_from_days():
    test_data = df_business.head(3)
    print(test_data["Saturday_Hour_Of_Opening_Float"])
    print("should be concatenated with")
    print(test_data["Sunday_Hour_Of_Opening_Float"])
    print("-------------------------------------------------------------")
    print(test_data["Saturday_Open_Duration_Float"])
    print("should be concatenated with")
    print(test_data["Sunday_Open_Duration_Float"])
    test_days = ["Saturday", "Sunday"]

    print("Test result:")
    test = get_concatenated_x_and_y_from_days(test_data, test_days)
    print(test)

# Complicated function to calculate the x, y, and z-values for the kernel density plot
# Borrowed from https://docs.bokeh.org/en/3.0.0/docs/examples/topics/stats/kde2d.html
def kde(x, y, N):
    xmin, xmax = x.min(), x.max()
    ymin, ymax = y.min(), y.max()

    X, Y = np.mgrid[xmin:xmax:N*1j, ymin:ymax:N*1j]
    positions = np.vstack([X.ravel(), Y.ravel()])
    values = np.vstack([x, y])
    kernel = gaussian_kde(values)
    Z = np.reshape(kernel(positions).T, X.shape)

    return X, Y, Z

# Create a bokeh contour glyph with the given arguments
def kde_plot(fig, x, y, color):
    x, y, z = kde(x, y, 100)
    levels = np.linspace(np.min(z), np.max(z), 6)
    contour = fig.contour(x, y, z, levels[1:], 
              #fill_color=color_palette, # Maybe we will use this in the future? Leaving it for now
              line_color=color)
    return contour

# Remove contours. Before computing new contours, we must remove the old ones to not
# see an overplotted mess.
def remove_contours():
    global contours_dict
    global fig
    for key, contours in contours_dict.items():
        for c in contours:
            if c in fig.renderers:
                fig.renderers.remove(c)
    contours_dict = {}

def compute_kernel_density_plots(attr, old, new):
    print("Computing contours...")
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
                        color=color_dict[rating_group])
        contour.name = "Contour_"+ rating_group # Not needed, but can be used for debugging
        contours_dict.setdefault(rating_group, []).append(contour)
    print("Finished computing contours")

# Function to delay firing of an event (namely the countor recomputation) for 2 seconds
def check_timeout():
    global last_press_time
    current_time = time.time()
    if current_time - last_press_time >= 1:
        print("No button pressed in the last 1 seconds: Triggering recompute.")
        # Arguments are required in order to compile, but we don't use them
        compute_kernel_density_plots(attr="active", old=[], new=[])

# Update the last press time
def delayer(attr, old, new):
    global last_press_time
    last_press_time = time.time()
    print("Button pressed: resetting timer.")
    curdoc().add_timeout_callback(check_timeout, 1000)

# --- Checkbox Events --- 

# When a weekday checkbox is checked/unchecked update the source_weekdays 
# data (JS callback) to reflect the checked boxes. When contours are 
# recomputed it will then recompute for the weekdays written in source_weekdays

update_weekdays_callback = CustomJS(args=dict(source_weekdays=source_weekdays, weekdays=weekdays, fig=fig), code="""
    let active = cb_obj.active;  // Get the indices of checked boxes
                                                    
    // Filter the weekdays based on the active indices
    let filtered_days = active.map(i => weekdays[i]);
    
    // Update the source_weekdays data to reflect the checked boxes
    source_weekdays.data = { days: filtered_days };
    source_weekdays.change.emit();  // Notify Bokeh that the data has changed                                          
""")


# Same as above but for rating groups 
update_rating_groups_callback = CustomJS(args=dict(source_rating_groups=source_rating_groups, rating_groups=rating_groups, fig=fig), code="""
    let active = cb_obj.active;  // Get the indices of checked boxes
                                                    
    // Filter the rating groups based on the active indices
    let filtered_rating_groups = active.map(i => rating_groups[i]);
                                                         
    // Update the rating_groups data to reflect the checked boxes                         
    source_rating_groups.data = { Rating_Groups: filtered_rating_groups };        
    source_rating_groups.change.emit();  // Notify Bokeh that the data has changed                                                                                              
""")

checkboxes_rating_groups.js_on_change('active', update_rating_groups_callback)
checkboxes_weekdays.js_on_change('active', update_weekdays_callback)

# Any change to any checkbox - whether rating group or weekday-related will
# call the delayer (Python callback), which after a delay will call compute_kernel_density_plots
checkboxes_weekdays.on_change("active", delayer)
checkboxes_rating_groups.on_change("active", delayer)

# Set up refresh button.
def refresh_btn_compute_kernel_density_plots():
    print("refresh btn clicked")
    compute_kernel_density_plots(attr="active", old=[], new=[])

# Python will complain if I pass in compute_kernel_density_plots because it expects 
# the attr="active", old=[], new=[] arguments. This is a quick workaround
btn_refresh.on_click(refresh_btn_compute_kernel_density_plots)

# --- Grid --- 

fig.grid.level = "overlay"
fig.grid.grid_line_color = "black"
fig.grid.grid_line_alpha = 0.05

# --- Legend --- 

# Hack to create static legends that are not hooked up to any renderers:
# Add dummy glyphs to represent legend items (not visible)
dummy_glyphs = []
for rating_group in rating_groups:
    dummy_glyphs.append(fig.scatter(1, 1, size=10, color=color_dict[rating_group], visible=False))

# Create a Legend manually with static items
legend_items = [
    LegendItem(label=rating_groups[i], renderers=[dummy_glyphs[i]])
    for i in range(len(rating_groups))
]
legend = Legend(items=legend_items)

# Add the legend to the figure
fig.add_layout(legend)  # Position it on the right

# --- Get the party started --- 

# Compute the first kernel density plot.
compute_kernel_density_plots(attr="active", old=[], new=[])

# Put the plot and buttons in a layout and add to the document
curdoc().add_root(column(checkboxes_rating_groups, checkboxes_weekdays, btn_refresh, fig))