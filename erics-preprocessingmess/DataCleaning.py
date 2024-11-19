import json

def filter_businesses_by_city(city_name):
    # Open the dataset and process line by line
    data = []
    with open('yelp_academic_dataset_business.json', encoding='utf-8') as f:
        for line in f:
            # Load each line as a separate JSON object
            business = json.loads(line)
            if business['city'] == city_name:
                data.append(business)

    # Save the filtered data into a new file
    with open('cleaned_business.json', 'w', encoding='utf-8') as outfile:
        json.dump(data, outfile, ensure_ascii=False, indent=4)

    # Print the number of businesses in Philadelphia
    print(f"Number of businesses in {city_name}: {len(data)}")

def filter_reviews(input_file, output_file):
    """Filters reviews to only include ids, stars, and date."""
    filtered_reviews = []

    # Open the review dataset and process line by line
    with open(input_file, encoding='utf-8') as f:
        for line in f:
            # Load each review as a JSON object
            review = json.loads(line)
            # Extract relevant fields
            filtered_review = {
                'review_id': review['review_id'],
                'business_id': review['business_id'],
                'stars': review['stars'],
                'date': review['date']
            }
            filtered_reviews.append(filtered_review)
    
    # Save the filtered reviews into a new file
    with open(output_file, 'w', encoding='utf-8') as outfile:
        json.dump(filtered_reviews, outfile, ensure_ascii=False, indent=4)
    
    # Print the number of filtered reviews
    print(f"Number of reviews filtered: {len(filtered_reviews)}")

def crosslist_reviews(business_file, review_file, output_file):
    """Filters reviews to only include those whose business_id is in the filtered business list."""
    
    # Load filtered business data (assuming it's already been filtered and saved)
    with open(business_file, encoding='utf-8') as f:
        filtered_businesses = json.load(f)
    
    # Create a set of business_ids from the filtered businesses
    business_ids = {business['business_id'] for business in filtered_businesses}
    
    crosslisted_reviews = []

    # Open the review dataset and process line by line
    with open(review_file, encoding='utf-8') as f:
        for line in f:
            # Load each review as a JSON object
            review = json.loads(line)
            # Check if the business_id in the review is in the set of filtered business_ids
            if review['business_id'] in business_ids:
                crosslisted_review = {
                    'review_id': review['review_id'],
                    'business_id': review['business_id'],
                    'stars': review['stars'],
                    'date': review['date']
                }
                crosslisted_reviews.append(crosslisted_review)
    
    # Save the crosslisted reviews into a new file
    with open(output_file, 'w', encoding='utf-8') as outfile:
        json.dump(crosslisted_reviews, outfile, ensure_ascii=False, indent=4)
    
    # Print the number of crosslisted reviews
    print(f"Number of crosslisted reviews: {len(crosslisted_reviews)}")
    
# For one city Philadelphia
filter_businesses_by_city('Philadelphia')

# Example usage for reviews:
filter_reviews('yelp_academic_dataset_review.json', 'cleaned_reviews.json')

# Example usage for crosslisting:
crosslist_reviews('cleaned_business.json', 'yelp_academic_dataset_review.json', 'crosslisted_reviews.json')
