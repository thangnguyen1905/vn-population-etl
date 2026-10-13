# Vietnam Population Data Integration & ETL Pipeline

An end-to-end Data Engineering portfolio project that integrates population statistics for Viet Nam from multiple sources, standardizes the data, loads it into PostgreSQL, validates data quality, and visualizes population trends using Power BI.

## 1. Project Overview

- **Country:** Viet Nam (VNM)
- **Period:** 2015–2024
- **Data Sources:** World Bank, United Nations WPP2024, Vietnam NSO
- **Standardized Observations:** 110

### Objectives

- Extract population data from a REST API and prepared CSV files.
- Clean and standardize heterogeneous datasets.
- Integrate observations while preserving source metadata.
- Store standardized data in PostgreSQL.
- Implement idempotent loading using UPSERT and database transactions.
- Perform SQL-based data quality checks and analysis.
- Visualize population trends and differences using Power BI.

## 2. Technology Stack

| Category | Technology |
|---|---|
| Programming | Python 3.12 |
| Data Processing | Pandas |
| API Integration | Requests |
| Database | PostgreSQL 17 |
| Database Connector | Psycopg 3 |
| Containerization | Docker & Docker Compose |
| Query Language | SQL |
| Visualization | Microsoft Power BI |
| Version Control | Git & GitHub |

## 3. Data Sources

### World Bank

Population data collected through the World Bank API using four indicators:

- SP.POP.TOTL — Total Population
- SP.POP.TOTL.MA.IN — Male Population
- SP.POP.TOTL.FE.IN — Female Population
- SP.POP.GROW — Population Growth Rate

### United Nations

Data from World Population Prospects 2024, including historical estimates for 2015–2023 and the Medium variant projection for 2024.

The original Excel data was manually filtered for Viet Nam and saved as two prepared CSV files.

### Vietnam NSO

Population statistics from table V02.02, including total, male, and female annual average population.

The current pipeline uses a manually prepared CSV exported from the NSO PX-Web system.

## 4. ETL Architecture

**Extract → Transform → Load → Validate → Analyze → Visualize**

**Extract:** Retrieve World Bank JSON data through its API and validate prepared CSV inputs from UN and NSO.

**Transform:** Standardize indicators, convert population values to persons, preserve data status, and produce a unified long-format dataset.

**Load:** Load standardized observations into PostgreSQL using parameterized SQL, UPSERT, and transactions.

**Validate:** Execute SQL checks for completeness, uniqueness, validity, and population consistency.

**Analyze:** Compare population estimates across sources and calculate year-over-year population growth.

**Visualize:** Build an interactive Power BI dashboard connected to PostgreSQL.

## 5. Key Features

- Modular Python ETL architecture
- World Bank API retry mechanism
- Offline extraction mode
- Extraction logging and manifests
- SHA-256 input checksums
- Standardized long-format dataset
- Source provenance and data-status metadata
- PostgreSQL constraints and UPSERT
- Transaction rollback testing
- Idempotent loading
- SQL data quality validation
- Power BI interactive dashboard

## 6. Project Results

| Metric | Result |
|---|---:|
| Data sources | 3 |
| Extracted input files | 7 |
| Standardized observations | 110 |
| Analyzed years | 10 |
| Data quality check groups | 5 |
| Duplicate business-key observations | 0 |

The loading process was tested for transaction rollback and idempotency.

Repeated loading of unchanged data resulted in zero affected rows, while retaining 110 observations in PostgreSQL.

## 7. Analytical Findings

- All three statistical sources indicate an increasing population in Viet Nam during 2015–2024.
- World Bank and UN population values are extremely close across the selected years.
- In 2024, Vietnam NSO reported 356,064 more persons than World Bank, corresponding to approximately 0.353% relative to the World Bank value.
- Calculated year-over-year growth trends differ across sources.

Differences between sources should not automatically be interpreted as data errors. Statistical definitions, reference periods, methods, and projection status must be considered.

## 8. Documentation

- `docs/data_sources.md` — Source descriptions and provenance.
- `docs/data_quality_report.md` — Data quality checks and analytical findings.
- `sql/01_create_population_observations.sql` — Database schema.
- `sql/02_data_quality_checks.sql` — SQL validation checks.
- `sql/03_population_analysis.sql` — Population analysis queries.

## 9. Dashboard

The Power BI dashboard includes:

- Population KPIs by source
- Population trends for 2015–2024
- NSO versus World Bank population differences
- Calculated year-over-year population growth
- Interactive year and source filters

Dashboard file: `dashboards/Vietnam_Population_Dashboard.pbix`

The UN 2024 population value is a Medium variant projection from WPP2024, not a historical observation.

## 10. Local Setup

Requirements:

- Python 3.12
- Docker and Docker Compose
- PostgreSQL client support through Psycopg
- Power BI Desktop (for dashboard exploration)

Clone the repository, create a Python virtual environment, install the dependencies, and configure `.env` using `.env.example`.

Start PostgreSQL using Docker Compose.

Prepare the UN and NSO CSV files according to the project data-source documentation before running the ETL pipeline.

Execute the pipeline in order:

1. `python src/run_extract.py`
2. `python src/run_transform.py`
3. Create the PostgreSQL schema using `sql/01_create_population_observations.sql`.
4. `python src/run_load.py`
5. Execute the SQL validation and analysis scripts.

The Extract step automates World Bank API collection. UN and NSO currently require manually prepared input files.

## 11. Limitations and Future Improvements

- Automate additional statistical data downloads where officially supported.
- Add automated unit and integration tests.
- Introduce scheduled pipeline execution.
- Improve statistical source and revision metadata.
- Extend analysis to additional countries or years.
- Develop a dimensional model for more advanced analytics.

## 12. License and Data Attribution

This project is intended for educational and portfolio purposes.

Population statistics are attributed to their respective providers: World Bank, United Nations Population Division, and Vietnam NSO. Use and redistribution of source datasets remain subject to the applicable provider terms.