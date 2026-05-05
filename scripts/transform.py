import pandas as pd
import numpy as np
from datetime import datetime
import logging
from typing import Tuple, Dict

logger = logging.getLogger(__name__)

class DataTransformer:
    def __init__(self):
        self.city_price_stats = {}
    
    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        logger.info("Starting data cleaning...")
        df = df.copy()

        original_count = len(df)

        # ✅ Remove duplicates (first pass)
        df = df.drop_duplicates(subset=['property_id'], keep='first')
        logger.info(f"Removed {original_count - len(df)} duplicate records")

        # ✅ Handle missing values
        if 'area_sqft' in df.columns:
            df.loc[:, 'area_sqft'] = df['area_sqft'].fillna(df['area_sqft'].median())

        if 'price' in df.columns and 'location' in df.columns:
            df.loc[:, 'price'] = df.groupby('location')['price'].transform(
                lambda x: x.fillna(x.median())
            )

        # ✅ Remove invalid rows
        df = df.dropna(subset=['price', 'area_sqft', 'location'])

        # ✅ Prevent division issues later
        df = df[df['area_sqft'] > 0]

        logger.info(f"Cleaned data: {len(df)} records remaining")
        return df
    
    def create_features(self, df: pd.DataFrame) -> pd.DataFrame:
        logger.info("Creating derived features...")
        df = df.copy()

        # ✅ Safe division
        df.loc[:, 'price_per_sqft'] = df['price'] / df['area_sqft']

        # City stats
        self.city_price_stats = df.groupby('location')['price'].agg(['mean', 'max']).to_dict()

        df.loc[:, 'city_avg_price'] = df.groupby('location')['price'].transform('mean')

        # Top locations
        city_avg_prices = df.groupby('location')['city_avg_price'].first().sort_values(ascending=False)
        top_percentile = city_avg_prices.quantile(0.75)
        top_locations = city_avg_prices[city_avg_prices >= top_percentile].index.tolist()

        df.loc[:, 'is_top_location'] = df['location'].isin(top_locations)

        logger.info(f"Identified {len(top_locations)} top locations")
        return df
    
    def format_dates(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()

        if 'listing_date' in df.columns:
            df.loc[:, 'listing_date'] = pd.to_datetime(df['listing_date'], errors='coerce').dt.date

        return df
    
    def validate_schema(self, df: pd.DataFrame) -> bool:
        expected_columns = [
            'property_id', 'price', 'location', 'area_sqft',
            'property_type', 'listing_date', 'bedrooms',
            'bathrooms', 'year_built'
        ]

        missing_columns = [col for col in expected_columns if col not in df.columns]

        if missing_columns:
            logger.error(f"Missing columns: {missing_columns}")
            return False

        if not pd.api.types.is_numeric_dtype(df['price']):
            logger.error("Price column is not numeric")
            return False

        if not pd.api.types.is_numeric_dtype(df['area_sqft']):
            logger.error("Area_sqft column is not numeric")
            return False

        logger.info("Schema validation passed")
        return True
    
    def transform(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict]:
        logger.info(f"Starting transformation with {len(df)} records")

        df = self.clean_data(df)
        df = self.format_dates(df)
        df = self.create_features(df)

        # ✅ FINAL DEDUP (IMPORTANT for idempotency)
        df = df.drop_duplicates(subset=['property_id'])

        if not self.validate_schema(df):
            raise ValueError("Schema validation failed")

        logger.info(f"Transformation completed: {len(df)} records")

        stats = {
            'total_records': len(df),
            'avg_price': df['price'].mean(),
            'avg_price_per_sqft': df['price_per_sqft'].mean(),
            'unique_locations': df['location'].nunique(),
            'city_stats': self.city_price_stats
        }

        return df, stats