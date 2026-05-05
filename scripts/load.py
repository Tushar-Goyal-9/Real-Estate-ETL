from scripts.db_utils import DatabaseManager
import pandas as pd
import logging
from datetime import datetime
from sqlalchemy import text

logger = logging.getLogger(__name__)

class DataLoader:
    def __init__(self):
        self.db_manager = DatabaseManager()
    
    def load_raw_data(self, df: pd.DataFrame) -> int:
        logger.info("Loading raw data to staging...")

        df = df.copy()

        raw_columns = [
            'property_id', 'price', 'location', 'area_sqft', 'property_type',
            'listing_date', 'bedrooms', 'bathrooms', 'year_built'
        ]

        existing_raw_cols = [col for col in raw_columns if col in df.columns]
        df_raw = df[existing_raw_cols].copy()

        # Convert timestamp safely
        if 'listing_date' in df_raw.columns:
            df_raw['listing_date'] = pd.to_datetime(
                df_raw['listing_date'], errors='coerce'
            ).dt.date

        df_raw['extracted_at'] = datetime.now()

        # ✅ Deduplicate
        df_raw = df_raw.drop_duplicates(subset=['property_id'])

        records_loaded = self.db_manager.load_data(
            df_raw, 'raw_properties', if_exists='append'
        )

        self._update_metadata('raw_properties', records_loaded, 'success')

        return records_loaded
    
    def load_transformed_data(self, df: pd.DataFrame) -> int:
        logger.info("Loading transformed data to analytics...")

        df = df.copy()

        # ✅ Fix date conversion safely
        if 'listing_date' in df.columns:
            df['listing_date'] = pd.to_datetime(
                df['listing_date'], errors='coerce'
            ).dt.date

        df['transformed_at'] = datetime.now()

        # ✅ FINAL DEDUP (IMPORTANT)
        df = df.drop_duplicates(subset=['property_id'])

        records_loaded = self.db_manager.load_data(
            df, 'transformed_properties', if_exists='append'
        )

        self._update_metadata('transformed_properties', records_loaded, 'success')

        return records_loaded
    
    def _update_metadata(self, table_name: str, record_count: int, status: str):
        query = text("""
            INSERT INTO etl_metadata (table_name, last_updated, record_count, status)
            VALUES (:table_name, NOW(), :record_count, :status)
        """)

        with self.db_manager.engine.begin() as conn:
            conn.execute(query, {
                "table_name": table_name,
                "record_count": record_count,
                "status": status
            })
    
    def initialize_database(self):
        self.db_manager.create_tables()
        logger.info("Database initialized successfully")
    
    def close(self):
        self.db_manager.close()