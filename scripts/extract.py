import pandas as pd
import requests
import json
from typing import Dict, Any
from datetime import datetime
import logging
import os

logger = logging.getLogger(__name__)

class DataExtractor:
    def __init__(self, source_type='csv', source_path=None):
        self.source_type = source_type
        self.source_path = source_path or 'data/raw/properties.csv'
    
    def extract_from_csv(self) -> pd.DataFrame:
        """Extract data from CSV file"""
        try:
            if not os.path.exists(self.source_path):
                raise FileNotFoundError(f"CSV file not found: {self.source_path}")
            
            df = pd.read_csv(self.source_path)
            logger.info(f"Extracted {len(df)} records from CSV: {self.source_path}")
            return df
        except Exception as e:
            logger.error(f"Error extracting from CSV: {e}")
            raise
    
    def extract_from_api(self, api_url: str, params: Dict = None) -> pd.DataFrame:
        """Extract data from API endpoint"""
        try:
            response = requests.get(api_url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if isinstance(data, list):
                df = pd.DataFrame(data)
            elif isinstance(data, dict) and 'results' in data:
                df = pd.DataFrame(data['results'])
            else:
                df = pd.DataFrame([data])
            
            logger.info(f"Extracted {len(df)} records from API: {api_url}")
            return df
        except Exception as e:
            logger.error(f"Error extracting from API: {e}")
            raise
    
    def extract(self, source_type=None, source_config=None) -> pd.DataFrame:
        """Main extract method"""
        source = source_type or self.source_type
        
        if source == 'csv':
            return self.extract_from_csv()
        elif source == 'api':
            api_url = source_config.get('url') if source_config else None
            params = source_config.get('params') if source_config else None
            return self.extract_from_api(api_url, params)
        else:
            raise ValueError(f"Unsupported source type: {source}")