import os
import pandas as pd
from sodapy import Socrata
from dotenv import load_dotenv  # Import the function to load the .env file

def load_activities():
    # Load environment variables from the .env file
    load_dotenv()

    # Load the token from environment variables
    app_token = os.getenv('APP_TOKEN')

    # Ensure that the token is present
    if app_token is None:
        raise ValueError("APP_TOKEN is missing from environment variables. Please add it to your .env file.")
    else:
        print("APP_TOKEN loaded successfully.")

    # Initialize the Socrata client with the token
    client = Socrata("data.cityofchicago.org", app_token)

    # Fetch the data
    results = client.get("tn7v-6rnw", limit=2000)

    # Convert to pandas DataFrame
    results_df = pd.DataFrame.from_records(results)
    #results_df.to_csv('chicago_parks_data.csv', index=False)