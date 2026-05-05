from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
import pandas as pd
import logging
from typing import Dict, Any
import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        self.db_config = {
            'host': os.getenv('POSTGRES_HOST', 'localhost'),
            'port': os.getenv('POSTGRES_PORT', '5432'),
            'database': os.getenv('POSTGRES_DB', 'real_estate_db'),
            'user': os.getenv('POSTGRES_USER', 'airflow'),
            'password': os.getenv('POSTGRES_PASSWORD', 'airflow')
        }
        self.engine = None
        self._create_engine()
    
    def _create_engine(self):
        """Create database engine"""
        connection_string = f"postgresql://{self.db_config['user']}:{self.db_config['password']}@{self.db_config['host']}:{self.db_config['port']}/{self.db_config['database']}"
        self.engine = create_engine(connection_string, echo=False)
    
    def create_tables(self):
        """Create necessary tables if they don't exist"""
        create_table_queries = [
            """
            CREATE TABLE IF NOT EXISTS raw_properties (
                id SERIAL PRIMARY KEY,
                property_id VARCHAR(255),
                price DECIMAL(15,2),
                location VARCHAR(255),
                area_sqft DECIMAL(10,2),
                property_type VARCHAR(100),
                listing_date DATE,
                bedrooms INTEGER,
                bathrooms INTEGER,
                year_built INTEGER,
                extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS transformed_properties (
                id SERIAL PRIMARY KEY,
                property_id VARCHAR(255),
                price DECIMAL(15,2),
                location VARCHAR(255),
                area_sqft DECIMAL(10,2),
                property_type VARCHAR(100),
                listing_date DATE,
                bedrooms INTEGER,
                bathrooms INTEGER,
                year_built INTEGER,
                price_per_sqft DECIMAL(15,2),
                city_avg_price DECIMAL(15,2),
                is_top_location BOOLEAN,
                transformed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS etl_metadata (
                id SERIAL PRIMARY KEY,
                table_name VARCHAR(100),
                last_updated TIMESTAMP,
                record_count INTEGER,
                status VARCHAR(50)
            )
            """
        ]
        
        try:
            with self.engine.begin() as conn:
                for query in create_table_queries:
                    conn.execute(text(query))
            logger.info("Database tables created successfully")
        except SQLAlchemyError as e:
            logger.error(f"Error creating tables: {e}")
            raise
    
    def load_data(self, df: pd.DataFrame, table_name: str, if_exists: str = 'append'):
        """Load dataframe to database"""
        try:
            df.to_sql(table_name, self.engine, if_exists=if_exists, index=False)
            logger.info(f"Loaded {len(df)} records to {table_name}")
            return len(df)
        except SQLAlchemyError as e:
            logger.error(f"Error loading data to {table_name}: {e}")
            raise
    
    def execute_query(self, query: str) -> pd.DataFrame:
        """Execute SQL query and return results"""
        try:
            return pd.read_sql(query, self.engine)
        except SQLAlchemyError as e:
            logger.error(f"Error executing query: {e}")
            raise
    
    def get_latest_etl_timestamp(self, table_name: str) -> pd.Timestamp:
        """Get latest ETL timestamp for incremental loading"""
        query = f"""
        SELECT MAX(extracted_at) as last_updated 
        FROM {table_name}
        """
        result = self.execute_query(query)
        return result['last_updated'].iloc[0] if not result.empty else None
    
    def close(self):
        """Close database connection"""
        if self.engine:
            self.engine.dispose()