import pandas as pd
import numpy as np
import json
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.impute import SimpleImputer
from sklearn.utils import resample

class DataCleaning:
    def __init__(self, file_path, file_type='csv'):
        """
        Initialize the DataCleaning class with the path to the dataset.
        """
        if file_type == 'csv':
            self.data = pd.read_csv(file_path)
        elif file_type == 'json':
            self.data = self.json_to_dataframe(file_path)
        else:
            raise ValueError("Unsupported file type. Use 'csv' or 'json'.")
        
        print(f"Loaded dataset with shape: {self.data.shape}")

    def json_to_dataframe(self, file_path):
        """
        Convert a JSON file to a Pandas DataFrame.
        """
        with open(file_path, 'r', encoding='utf-8') as file:
            json_data = json.load(file)
        
        if isinstance(json_data, dict):
            df = pd.DataFrame(json_data)
        elif isinstance(json_data, list):
            df = pd.DataFrame.from_records(json_data)
        else:
            raise ValueError("Invalid JSON format. Expected a list of dictionaries or a dictionary of lists.")
        
        print(f"Converted JSON to DataFrame with shape: {df.shape}")
        return df

    def save_as_csv(self, output_path='output.csv'):
        """
        Save the loaded dataset as a CSV file.
        """
        self.data.to_csv(output_path, index=False)
        print(f"Data saved to {output_path}")
    
    def normalize_dictionary_columns(self):
        """
        Normalize and expand dictionary columns like 'attributes' and 'hours'.
        """
        for column in self.data.columns:
            if self.data[column].apply(lambda x: isinstance(x, dict)).sum() > 0:
                print(f"Normalizing column: {column}")
                expanded_cols = pd.json_normalize(self.data[column])
                expanded_cols = expanded_cols.add_prefix(f'{column}_')
                self.data.drop(column, axis=1, inplace=True)
                self.data = pd.concat([self.data, expanded_cols], axis=1)
        
        print(f"Data shape after normalizing dictionary columns: {self.data.shape}")

    def visualize_missingness(self, data=None):
        """
        Visualize missing values in the dataset using a heatmap.
        If no data is passed, visualize the main dataset.
        """
        if data is None:
            data = self.data
        plt.figure(figsize=(12, 8))
        sns.heatmap(data.isnull(), cbar=False, cmap='viridis')
        plt.title("Missing Values Heatmap")
        plt.show()

    def data_quality_tests(self, data=None):
        """
        Run basic tests to assess data quality and report issues.
        If no data is passed, perform tests on the main dataset.
        """
        if data is None:
            data = self.data
        print("Summary statistics:")
        print(data.describe())
        print("\nMissing values per column:")
        print(data.isnull().sum())
        
        print("\nChecking for inconsistencies...")
        if data.duplicated().sum() > 0:
            print("Warning: There are duplicate rows in the dataset.")
        else:
            print("No duplicate rows detected.")
        
        for col in data.select_dtypes(include=[np.number]):
            print(f"Checking range of {col}: {data[col].min()} to {data[col].max()}")
    
    def handle_missing_values(self, strategy='mean', data=None):
        """
        Handle missing values based on the specified strategy.
        If no data is passed, handle missing values for the main dataset.
        """
        if data is None:
            data = self.data
        if strategy == 'drop':
            initial_shape = data.shape
            data.dropna(inplace=True)
            print(f"Removed {initial_shape[0] - data.shape[0]} rows with missing values.")
        else:
            imputer = SimpleImputer(strategy=strategy)
            data.iloc[:, :] = imputer.fit_transform(data)
            print(f"Missing values filled using strategy: {strategy}")
    
    def remove_duplicates(self, data=None):
        """
        Remove duplicate rows in the dataset.
        If no data is passed, remove duplicates in the main dataset.
        """
        if data is None:
            data = self.data
        initial_shape = data.shape
        data.drop_duplicates(inplace=True)
        print(f"Removed {initial_shape[0] - data.shape[0]} duplicate rows.")

    def analyze_data_points(self, data=None):
        """
        Display the number of data points and check if sampling is required.
        If no data is passed, analyze the main dataset.
        """
        if data is None:
            data = self.data
        print(f"Total data points after cleaning: {data.shape[0]}")
        if data.shape[0] > 10000:
            print("Large dataset detected. Consider sampling for further analysis.")
        else:
            print("Dataset size is manageable for analysis.")

    def perform_sampling(self, method='random', sample_fraction=0.1):
        """
        Perform sampling on the dataset to reduce its size for analysis.
        Options for method: 'random' or 'stratified' (requires 'target_column').
        """
        if method == 'random':
            sampled_data = self.data.sample(frac=sample_fraction, random_state=42)
            print(f"Randomly sampled {sample_fraction*100}% of the dataset.")
        elif method == 'stratified':
            target_column = input("Enter the target column name for stratified sampling: ")
            sampled_data = resample(self.data, stratify=self.data[target_column], n_samples=int(sample_fraction * len(self.data)))
            print(f"Stratified sampled {sample_fraction*100}% of the dataset based on column: {target_column}")
        
        self.data_sample = sampled_data
        return self.data_sample

    def save_cleaned_data(self, output_path='cleaned_data.csv', data=None):
        """
        Save the cleaned dataset to a new CSV file.
        If no data is passed, save the main dataset.
        """
        if data is None:
            data = self.data
        data.to_csv(output_path, index=False)
        print(f"Cleaned dataset saved to {output_path}")
    
    def write_report(self, report_path='data_cleaning_report.txt'):
        """
        Write a summary report of the data cleaning process to a text file.
        """
        with open(report_path, 'w') as report_file:
            report_file.write(f"Data Cleaning Report\n")
            report_file.write(f"{'='*40}\n")
            report_file.write(f"Dataset shape: {self.data.shape}\n\n")
            
            # Summary statistics
            report_file.write("Summary Statistics:\n")
            report_file.write(f"{self.data.describe()}\n\n")
            
            # Missing values
            report_file.write("Missing Values per Column:\n")
            report_file.write(f"{self.data.isnull().sum()}\n\n")
            
            # Duplicate check
            duplicates = self.data.duplicated().sum()
            report_file.write(f"Duplicate rows: {duplicates}\n\n")
            
            # Column ranges
            report_file.write("Numeric Column Ranges:\n")
            for col in self.data.select_dtypes(include=[np.number]):
                report_file.write(f"{col}: {self.data[col].min()} to {self.data[col].max()}\n")
            
            report_file.write("\nReport complete.\n")
        print(f"Report written to {report_path}")

# Example usage:
cities = ['Tucson', 'Tampa']
for i in cities:
    cleaner = DataCleaning('crosslisted_reviews_' + i + '.json', file_type='json')
    cleaner.normalize_dictionary_columns()  # Normalize dictionary columns like 'attributes' and 'hours'
    cleaner.save_as_csv('crosslisted_reviews_' + i + '.csv')  # Save the initial JSON as CSV
    cleaner.visualize_missingness()  # Visualize missingness of the full dataset
    cleaner.data_quality_tests()  # Perform data quality checks on the full dataset
    cleaner.handle_missing_values(strategy='drop')  # Handle missing values for full dataset
    cleaner.remove_duplicates()  # Remove duplicates from full dataset
    cleaner.analyze_data_points()  # Analyze data points in the full dataset
    # cleaner.write_report('cleaned_business_' + i + '.txt')  # Write a report summarizing the cleaning steps
    # sampled_data = cleaner.perform_sampling(method='random', sample_fraction=0.1)  # Perform random sampling


    # Perform all tests and processing on the sample
    print("\n=== Data Quality Tests for the Sample ===")
    # cleaner.visualize_missingness(data=sampled_data)  # Visualize missingness of the sample
    # cleaner.data_quality_tests(data=sampled_data)  # Perform data quality checks on the sample
    # cleaner.handle_missing_values(strategy='mean', data=sampled_data)  # Handle missing values for the sample
    # cleaner.remove_duplicates(data=sampled_data)  # Remove duplicates from the sample
    # cleaner.analyze_data_points(data=sampled_data)  # Analyze data points in the sample
    # cleaner.save_cleaned_data('crosslisted_reviews_sample_data.csv', data=sampled_data)  # Save the cleaned sample
    # cleaner.write_report('crosslisted_reviews_sample_report.txt')  # Write a report summarizing the cleaning steps