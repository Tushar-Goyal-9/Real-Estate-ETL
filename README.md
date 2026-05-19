# 📊 Real Estate ETL Pipeline – Production Data Engineering

A production-grade **ETL (Extract, Transform, Load)** pipeline that processes real estate property data using **Apache Airflow, PostgreSQL, Python, Docker, and Streamlit**.

The pipeline extracts raw property data from CSV/API sources, cleans and enriches it, loads transformed data into PostgreSQL, and provides real-time analytics through an interactive dashboard.

---

# 📌 Project Overview

This project builds an automated, production-ready ETL pipeline that:

- Extracts property data from CSV files or external APIs
- Cleans missing values, removes duplicates, and standardizes formats
- Creates business metrics such as:
  - `price_per_sqft`
  - `city_avg_price`
- Loads raw and transformed data into PostgreSQL
- Orchestrates workflow with Apache Airflow
- Visualizes insights using Streamlit

---

# 🛠️ Tech Stack Used

## ETL & Orchestration

- Apache Airflow — Workflow orchestration and scheduling
- Python 3.9 — Core ETL logic
- Pandas — Data cleaning and transformation
- SQLAlchemy — Database interaction

## Database

- PostgreSQL 13 — Staging + analytics data warehouse

## Containerization

- Docker
- Docker Compose

## Dashboard & Visualization

- Streamlit — Interactive analytics dashboard

## Utilities

- Faker — Synthetic data generation
- python-dotenv — Environment variable management
- Requests — API extraction
- Psycopg2 — PostgreSQL adapter

---

# 📂 Project Structure

```text
real_estate_etl/
│
├── dags/
│   └── real_estate_etl_dag.py
│
├── scripts/
│   ├── __init__.py
│   ├── extract.py
│   ├── transform.py
│   ├── load.py
│   ├── utils.py
│   └── db_utils.py
│
├── dashboard/
│   └── app.py
│
├── data/
│   ├── raw/
│   └── sample_data_generator.py
│
├── sql/
│   ├── analysis_queries.sql
│   └── init_db.sql
│
├── config/
│   └── config.yaml
│
├── logs/
│
├── .env
├── .gitignore
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── README.md
```

---

# ✨ Key Features

## ETL Pipeline

- Automated daily execution via Apache Airflow
- Incremental loading support
- Schema/data quality validation
- Duplicate removal
- Feature engineering
- Retry logic with exponential backoff
- Detailed logging
- Metadata tracking
- Separate staging + analytics layers

---

## Data Transformations

- Clean null/missing values
- Median imputation
- Duplicate removal
- PostgreSQL date formatting
- Derived metrics:

```python
price_per_sqft = price / area_sqft
```

- City average price calculation
- Top 25% expensive location flagging

---

## Dashboard Features

- Interactive filters
- KPI cards
- Charts and visualizations
- CSV export
- Real-time PostgreSQL connection

---

## Security & Best Practices

- Environment variables for secrets
- No hardcoded credentials
- Docker isolation
- Connection pooling
- Error handling + retries

---

# 🔄 ETL Workflow (Airflow DAG)

```text
[Start]
   ↓
[Extract Task]
   ↓
[Transform Task]
   ↓
[Validate Task]
   ↓
[Load Task]
   ↓
[End]
```

## Task Details

| Task | Description |
|------|-------------|
| Extract | Reads CSV/API data and pushes raw DataFrame |
| Transform | Cleans data and adds derived columns |
| Validate | Performs quality checks |
| Load | Loads raw + transformed data into PostgreSQL |

### Configuration

- Schedule: `@daily`
- Retries: 3
- Retry delay: 5 minutes
- Logs accessible via Airflow UI

---

# 📊 Database Schema

## raw_properties

| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL | Primary key |
| property_id | VARCHAR(255) | Unique identifier |
| price | DECIMAL(15,2) | Property price |
| location | VARCHAR(255) | City |
| area_sqft | DECIMAL(10,2) | Property area |
| property_type | VARCHAR(100) | Apartment / House / Condo |
| listing_date | DATE | Listing date |
| bedrooms | INTEGER | Bedroom count |
| bathrooms | INTEGER | Bathroom count |
| year_built | INTEGER | Construction year |
| extracted_at | TIMESTAMP | ETL extraction timestamp |

---

## transformed_properties

Includes all raw columns plus:

| Column | Type | Description |
|--------|------|-------------|
| price_per_sqft | DECIMAL(15,2) | Price ÷ area |
| city_avg_price | DECIMAL(15,2) | Avg city price |
| is_top_location | BOOLEAN | Top 25% expensive |
| transformed_at | TIMESTAMP | Transformation timestamp |

---

## etl_metadata

| Column | Type | Description |
|--------|------|-------------|
| table_name | VARCHAR(100) | Updated table |
| last_updated | TIMESTAMP | Update timestamp |
| record_count | INTEGER | Inserted rows |
| status | VARCHAR(50) | Success/failure |

---

# 🚀 How to Run Locally

## Prerequisites

Install:

- Docker Desktop
- WSL2 (Windows)
- Git
- Minimum 4GB Docker RAM

---

## 1. Clone Repository

```bash
git clone https://github.com/Tushar-Goyal-9/real-estate-etl-pipeline.git
cd real-estate-etl-pipeline
```

---

## 2. Configure Environment Variables

Create `.env`:

```env
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=real_estate_db
POSTGRES_USER=airflow
POSTGRES_PASSWORD=airflow
```

---

## 3. Generate Sample Data

```bash
docker-compose exec webserver mkdir -p /opt/airflow/data/raw
docker-compose exec webserver python /opt/airflow/data/sample_data_generator.py
```

Creates:

```text
data/raw/properties.csv
```

---

## 4. Start Services

```bash
docker-compose up -d
```

Starts:

- PostgreSQL
- Airflow Webserver
- Airflow Scheduler
- Metadata Database

---

## 5. Access Airflow UI

Open:

```text
http://localhost:8080
```

Login:

```text
Username: admin
Password: admin
```

---

## 6. Trigger the DAG

- Find DAG: `real_estate_etl_pipeline`
- Unpause DAG
- Trigger DAG manually
- Watch task execution:

```text
extract_task
transform_task
validate_task
load_task
```

---

## 7. Verify PostgreSQL Data

```bash
docker-compose exec postgres psql -U airflow -d real_estate_db -c "SELECT COUNT(*) FROM transformed_properties;"
```

Expected:

```text
1000
```

(or matching CSV count)

---

## 8. Run Streamlit Dashboard

Install:

```bash
pip install streamlit pandas psycopg2-binary sqlalchemy
```

Run:

```bash
streamlit run dashboard/app.py
```

Open:

```text
http://localhost:8501
```

---


# 📚 Sample SQL Queries

## Average Price Per City

```sql
SELECT location, COUNT(*) AS count, ROUND(AVG(price), 0) AS avg_price
FROM transformed_properties
GROUP BY location
ORDER BY avg_price DESC;
```

## Top 5 Expensive Locations

```sql
SELECT location, ROUND(AVG(price_per_sqft), 0) AS avg_price_sqft
FROM transformed_properties
GROUP BY location
ORDER BY avg_price_sqft DESC
LIMIT 5;
```

## Property Type Analysis

```sql
SELECT property_type, COUNT(*) AS count, ROUND(AVG(price), 0) AS avg_price
FROM transformed_properties
GROUP BY property_type;
```

## Monthly Trends

```sql
SELECT DATE_TRUNC('month', listing_date) AS month, COUNT(*) AS listings
FROM transformed_properties
GROUP BY month
ORDER BY month DESC;
```

## ETL Metadata

```sql
SELECT table_name, last_updated, record_count, status
FROM etl_metadata
ORDER BY last_updated DESC;
```

---

# 📚 Learning Outcomes

This project helped me learn:

- ETL architecture design
- Apache Airflow DAG orchestration
- Task scheduling + dependencies
- XCom communication
- Pandas transformations
- PostgreSQL schema design
- Docker container orchestration
- Environment variable management
- Retry/error handling
- Incremental ETL concepts
- Data validation techniques
- Streamlit dashboard development

---

# 👨‍💻 Developer

**Tushar Goyal**

- GitHub: https://github.com/Tushar-Goyal-9

---

# ⭐ Future Enhancements

Planned upgrades:

- API data extraction
- Email alerts
- Data quality monitoring dashboard
- Parquet support
- ML price prediction
- Snowflake / BigQuery support
- Terraform deployment
- Real-time streaming ETL

---

# 📄 License

This project is for educational purposes.

---

# 🙏 Acknowledgements

- Apache Airflow
- PostgreSQL
- Streamlit
- Docker
- Faker

---

# 🤝 Contributing

Contributions, suggestions, and feature requests are welcome.

Open an issue or submit a pull request.

---

# ⭐ Support

If this project helped you, please give it a star on GitHub!
