import sys
import os
import logging
import pandas as pd
import pendulum

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.empty import EmptyOperator  # modern replacement
from airflow.models import Variable

# ----------------------------
# PATH SETUP
# ----------------------------
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from scripts.extract import DataExtractor
from scripts.transform import DataTransformer
from scripts.load import DataLoader
from scripts.utils import log_metrics

# ----------------------------
# TIMEZONE (IST)
# ----------------------------
local_tz = pendulum.timezone("Asia/Kolkata")

# ----------------------------
# DEFAULT ARGS
# ----------------------------
default_args = {
    'owner': 'data_team',
    'depends_on_past': False,
    'start_date': datetime(2026, 5, 1, tzinfo=local_tz),  # ✅ FIXED TIMEZONE
    'email_on_failure': True,
    'email_on_retry': False,
    'email': ['admin@example.com'],
    'retries': 3,
    'retry_delay': timedelta(minutes=5)
}

# ----------------------------
# TASK FUNCTIONS
# ----------------------------

def extract_data(**context):
    logger = logging.getLogger(__name__)
    start_time = datetime.now()

    source_type = Variable.get("data_source_type", default_var="csv")
    source_path = Variable.get(
        "csv_source_path",
        default_var="/opt/airflow/data/raw/properties.csv"
    )

    extractor = DataExtractor(source_type=source_type, source_path=source_path)
    df = extractor.extract()

    context['ti'].xcom_push(key='extracted_data', value=df.to_json())

    log_metrics('extract', start_time, datetime.now(), len(df))
    return f"Extracted {len(df)} records"


def transform_data(**context):
    logger = logging.getLogger(__name__)
    start_time = datetime.now()

    ti = context['ti']
    df_json = ti.xcom_pull(key='extracted_data', task_ids='extract_task')

    df = pd.read_json(df_json)

    transformer = DataTransformer()
    transformed_df, stats = transformer.transform(df)

    ti.xcom_push(key='transformed_data', value=transformed_df.to_json())
    ti.xcom_push(key='transform_stats', value=stats)

    log_metrics('transform', start_time, datetime.now(), len(transformed_df))
    return f"Transformed {len(transformed_df)} records"


def validate_data(**context):
    logger = logging.getLogger(__name__)

    ti = context['ti']
    stats = ti.xcom_pull(key='transform_stats', task_ids='transform_task')

    if stats['total_records'] < 10:
        raise ValueError("Insufficient data records")

    if stats['avg_price'] <= 0:
        raise ValueError("Invalid average price detected")

    logger.info(f"Validation passed: {stats}")
    return "Validation passed"


def load_data(**context):
    logger = logging.getLogger(__name__)
    start_time = datetime.now()

    ti = context['ti']
    df_json = ti.xcom_pull(key='transformed_data', task_ids='transform_task')

    df = pd.read_json(df_json)

    loader = DataLoader()
    loader.initialize_database()

    raw_count = loader.load_raw_data(df.copy())
    transformed_count = loader.load_transformed_data(df)

    loader.close()

    log_metrics('load', start_time, datetime.now(), transformed_count)
    return f"Loaded {transformed_count} records (Raw: {raw_count})"


# ----------------------------
# DAG DEFINITION
# ----------------------------
with DAG(
    dag_id='real_estate_etl_pipeline',
    default_args=default_args,
    description='ETL pipeline for real estate property data',
    schedule_interval=None,   # ✅ manual only
    catchup=False,            # ✅ no backfill
    max_active_runs=1,
    tags=['real_estate', 'etl'],
) as dag:

    # ----------------------------
    # TASKS
    # ----------------------------
    start_task = EmptyOperator(task_id='start')

    extract_task = PythonOperator(
        task_id='extract_task',
        python_callable=extract_data
    )

    transform_task = PythonOperator(
        task_id='transform_task',
        python_callable=transform_data
    )

    validate_task = PythonOperator(
        task_id='validate_task',
        python_callable=validate_data
    )

    load_task = PythonOperator(
        task_id='load_task',
        python_callable=load_data
    )

    end_task = EmptyOperator(task_id='end')

    # ----------------------------
    # FLOW
    # ----------------------------
    start_task >> extract_task >> transform_task >> validate_task >> load_task >> end_task