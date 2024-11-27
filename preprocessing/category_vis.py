from typing import Counter
import pandas as pd
# import plotly.express as px
import json

#TEMP CODE TO SELECT CITIES
city_counts = Counter()
with open('yelp_academic_dataset_business.json', encoding='utf-8') as f:
    for line in f:
        data = json.loads(line)
        if 'city' in data:
            city_counts[data['city']] += 1

top_city = city_counts.most_common(20)
for city, count in top_city:
    print(f"{city}: {count}")
print(f"\nTotal unique cities: {len(city_counts)}")

        


# # Load the cleaned CSV file
# csv_file_path = 'cleaned_business.csv'
# df = pd.read_csv(csv_file_path)

# # Split the 'categories' column into individual categories (assuming multiple categories are separated by commas)
# df['categories'] = df['categories'].str.split(',')

# # Explode the categories into separate rows
# df_exploded = df.explode('categories')

# # Clean up category names (remove leading/trailing whitespace)
# df_exploded['categories'] = df_exploded['categories'].str.strip()

# # Exclude rows where 'categories' is 'Restaurant' (or contains 'Restaurant' in the name)
# df_exploded = df_exploded[~df_exploded['categories'].str.contains('restaurant', case=False, na=False)]

# # Count the number of occurrences of each category
# category_counts = df_exploded['categories'].value_counts()

# # Get the top N categories
# N = 20  # Number of categories to display, adjust as necessary
# top_categories = category_counts.head(N)

# # Total number of businesses (excluding restaurants)
# total_businesses = df_exploded.shape[0]

# # Calculate the percentage for each top category
# top_categories_percentages = (top_categories / total_businesses) * 100

# # Create an interactive bar chart using Plotly
# fig = px.bar(
#     top_categories, 
#     x=top_categories.index, 
#     y=top_categories.values, 
#     title="Top Business Categories (Excluding Restaurants)",
#     labels={"x": "Category", "y": "Number of Businesses"},
#     hover_data={"Number of Businesses": top_categories.values, "Percentage": top_categories_percentages.values.round(2)},  # Hover data for business counts
#     color=top_categories.index,  # Set different colors for each category
#     color_discrete_sequence=px.colors.qualitative.Set1 
# )

# # Update layout for better display
# fig.update_layout(
#     xaxis_tickangle=-45,  # Rotate x-axis labels for better readability
#     title_x=0.5,  # Center the title
#     showlegend=False,  # Hide the legend (colors are self-explanatory in this case)
#     hoverlabel=dict(bgcolor="white", font_size=12, font_family="Rockwell")
# )

# # Add a note about excluding restaurants
# fig.add_annotation(
#     text="Note: 'Restaurant' category was excluded from the chart as it is common to all businesses.",
#     xref="paper", yref="paper",
#     x=0.83, y=0.95, showarrow=False,
#     font=dict(size=10),
#     xanchor='center'
# )

# # Show the plot
# fig.show()

# unique_categories_count = df_exploded['categories'].nunique()

# # Create a pie chart to show the number of unique categories
# fig_pie = px.pie(
#     names=["Unique Categories (Excluding Restaurant)", "Restaurant (excluded)"],
#     values=[unique_categories_count, 1],  # Placeholder for 'Restaurant' as excluded
#     title="Total Number of Unique Categories (Excluding Restaurants)",
#     hole=0.4  # Donut chart style
# )

# # Update layout for the pie chart
# fig_pie.update_layout(
#     title_x=0.5,  # Center the title
# )

# # Show the pie chart
# fig_pie.show()