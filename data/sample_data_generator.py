import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from faker import Faker
import random

fake = Faker()

def generate_property_data(num_records=1000):
    """Generate synthetic property data"""
    
    cities = ['New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix', 
              'Philadelphia', 'San Antonio', 'San Diego', 'Dallas', 'San Jose']
    
    property_types = ['Apartment', 'House', 'Condo', 'Townhouse', 'Villa']
    
    data = []
    
    for _ in range(num_records):
        city = random.choice(cities)
        area_sqft = random.randint(500, 5000)
        
        # Price depends on city and area
        base_price_per_sqft = {
            'New York': 1200, 'Los Angeles': 800, 'Chicago': 300,
            'Houston': 200, 'Phoenix': 250, 'Philadelphia': 200,
            'San Antonio': 180, 'San Diego': 600, 'Dallas': 220,
            'San Jose': 900
        }
        
        price = area_sqft * base_price_per_sqft[city] * random.uniform(0.8, 1.2)
        
        # Add some noise and missing values
        if random.random() < 0.05:  # 5% missing values
            price = np.nan
        if random.random() < 0.03:  # 3% missing area
            area_sqft = np.nan
            
        record = {
            'property_id': fake.uuid4(),
            'price': round(price, 2) if not pd.isna(price) else None,
            'location': city,
            'area_sqft': area_sqft if not pd.isna(area_sqft) else None,
            'property_type': random.choice(property_types),
            'listing_date': fake.date_between(start_date='-1y', end_date='today'),
            'bedrooms': random.randint(1, 5),
            'bathrooms': random.randint(1, 4),
            'year_built': random.randint(1950, 2023)
        }
        data.append(record)
    
    df = pd.DataFrame(data)
    
    # Add some duplicate records
    duplicates = df.sample(n=int(num_records * 0.02))
    df = pd.concat([df, duplicates], ignore_index=True)
    
    # Shuffle the dataframe
    df = df.sample(frac=1).reset_index(drop=True)
    
    return df

if __name__ == "__main__":
    # Generate 1000 records
    df = generate_property_data(1000)
    
    # Save to CSV
    df.to_csv('data/raw/properties.csv', index=False)
    print(f"Generated {len(df)} property records")
    print(f"Saved to data/raw/properties.csv")
    print("\nSample data:")
    print(df.head())
    print(f"\nData types:\n{df.dtypes}")