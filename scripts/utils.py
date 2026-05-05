import logging
import sys
from datetime import datetime
import yaml
import os

def setup_logging(log_level=logging.INFO):
    """Setup logging configuration"""
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(f'logs/etl_{datetime.now().strftime("%Y%m%d")}.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

def load_config(config_path='config/config.yaml'):
    """Load configuration from YAML file"""
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    return {}

def log_metrics(step: str, start_time: datetime, end_time: datetime, record_count: int):
    """Log ETL metrics"""
    duration = (end_time - start_time).total_seconds()
    logger = logging.getLogger(__name__)
    logger.info(f"ETL Step: {step} | Duration: {duration}s | Records: {record_count}")