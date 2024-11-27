import pandas as pd

# Function to fix the time format (adding leading zeros where necessary)
def fill_missing_zeros(time_str):
    if pd.isna(time_str) or time_str == '0:0-0:0':
        return 'Closed'
    time_ranges = time_str.split('-')
    fixed_time = []
    for time_range in time_ranges:
        hours, minutes = time_range.split(':')
        # Add leading zero if necessary
        fixed_hours = hours.zfill(2)
        fixed_minutes = minutes.zfill(2)
        fixed_time.append(f"{fixed_hours}:{fixed_minutes}")
    return '-'.join(fixed_time)


# Load the CSV file
for i in 'Tucson', 'Tampa':
    csv_file_path = 'cleaned_business_' + i + '.csv'
    df = pd.read_csv(csv_file_path)

    # Drop all columns related to attributes (columns that start with 'attributes_')
    df = df[df.columns.drop(list(df.filter(regex='attributes_')))]

    # Filter rows where the 'categories' column contains the word "Restaurant" (case insensitive)
    df_filtered = df[df['categories'].str.contains("restaurant", case=False, na=False)].copy()

    # Apply the function to fix the time format for columns generated from the 'hours' dictionary
    for day in ['hours_Monday', 'hours_Tuesday', 'hours_Wednesday', 'hours_Thursday', 'hours_Friday', 'hours_Saturday', 'hours_Sunday']:
        if day in df_filtered.columns:
            df_filtered[day] = df_filtered[day].apply(fill_missing_zeros)
    # Save the cleaned and filtered data to a new CSV file
    filename = 'cleaned_businessV2_' + i + '.csv'
    df_filtered.to_csv(filename, index=False)

    print("Data cleaned and saved to " + filename)
