# Local Setup & Reproducibility Guide

## 1. Prerequisites

This project was developed using:

- Windows 10
- Python 3.12
- Docker Desktop and Docker Compose
- PostgreSQL 17 (Docker)
- Git
- Power BI Desktop (optional, for visualization)

## 2. Clone the Repository

Open Windows CMD:

```bat
git clone https://github.com/thangnguyen1905/vn-population-etl.git
cd vn-population-etl
```

## 3. Set Up Python

Create and activate a virtual environment:

```bat
python -m venv .venv
.venv\Scripts\activate.bat
```

Install Python dependencies:

```bat
python -m pip install -r requirements.txt
```

## 4. Configure Environment Variables

Copy the example environment file:

```bat
copy .env.example .env
```

Update `.env` to match the local PostgreSQL configuration.

Example:

```dotenv
DB_HOST=127.0.0.1
DB_PORT=5434
DB_NAME=population_db
DB_USER=population_user
DB_PASSWORD=YOUR_LOCAL_PASSWORD
```

The password must match the PostgreSQL container configuration.

**Security:** Never commit `.env` or real database credentials.

## 5. Start PostgreSQL

Start the database container:

```bat
docker compose up -d
```

Verify that PostgreSQL is running:

```bat
docker ps
```

Check the database connection:

```bat
python src\check_connection.py
```

The expected result is a successful connection to `population_db`.

The development configuration uses host port `5434`. Adjust the port if required by your local Docker configuration.

## 6. Prepare Raw Datasets

The pipeline uses three data providers.

### World Bank

World Bank data is downloaded automatically from the API by `run_extract.py`.

Indicators:

- `SP.POP.TOTL`
- `SP.POP.TOTL.MA.IN`
- `SP.POP.TOTL.FE.IN`
- `SP.POP.GROW`

### United Nations

Source: World Population Prospects 2024.

The original UN workbook is manually prepared as two CSV inputs:

- `WPP2024_GEN_F01_DEMOGRAPHIC_INDICATORS_COMPACT_VN_Estimates.csv`
- `WPP2024_GEN_F01_DEMOGRAPHIC_INDICATORS_COMPACT_VN_Medium_variant.csv`

Place them in:

`data/raw/un/`

The prepared CSV files must preserve the required population columns, the country code `VNM`, `Variant`, and `Year`.

The files are derived from the Estimates and Medium variant worksheets. Unrelated countries and unused indicator groups were removed manually.

The prepared files contain one header row and retain population figures in thousands.

### Vietnam NSO

Source: NSO PX-Web table V02.02.

Export average population by sex for the years 2015–2024, selecting total population, male population and female population.

Prepare a CSV with these five fields in this order:

```csv
Cach tinh,Nam,Tong so,Nam,Nu
```

Keep the original statistical values in thousands of persons. The first column should contain `Tong so (Nghin nguoi)`.

Save the prepared file as:

`data/raw/nso/V02.02.csv`

The current NSO parser requires this prepared five-column format.

**Important:** The UN and NSO sources are not downloaded automatically in the current pipeline. The manual preparation procedures must be followed before running extraction.

## 7. Run Extraction

For online extraction:

```bat
python src\run_extract.py
```

This downloads World Bank data and validates local UN and NSO CSV files.

For offline extraction using existing World Bank JSON files:

```bat
python src\run_extract.py --offline
```

The offline mode requires World Bank JSON files to be available locally.

Expected result:

```text
Status: success | Files: 7 | Selected rows: 60
```

## 8. Run Transformation

```bat
python src\run_transform.py
```

The transformation stage standardizes source indicators, converts population figures to persons, preserves metadata, and validates data quality.

Expected output:

`data/processed/population_long_2015_2024.csv`

Expected result:

```text
Transform SUCCESS: 110 rows, 13 columns
```

## 9. Create the Database Schema

Run from Windows CMD:

```bat
docker exec -i vn-population-postgres psql -v ON_ERROR_STOP=1 -U population_user -d population_db < sql\01_create_population_observations.sql
```

This creates the `public.population_observations` table.

The command assumes the container name and database credentials match the development configuration.

## 10. Load Data into PostgreSQL

```bat
python src\run_load.py
```

Expected result for an initially empty table:

```text
LOAD SUCCESS | Affected: 110 | Total in DB: 110
```

Running the same Loader again with unchanged inputs should not create duplicate observations.

The loader uses PostgreSQL UPSERT and transactions.

## 11. Run Data Quality Checks

```bat
docker exec -i vn-population-postgres psql -X -v ON_ERROR_STOP=1 -U population_user -d population_db < sql\02_data_quality_checks.sql
```

The SQL checks cover completeness, missing observations, uniqueness, validity and population consistency.

## 12. Run Population Analysis

```bat
docker exec -i vn-population-postgres psql -X -v ON_ERROR_STOP=1 -U population_user -d population_db < sql\03_population_analysis.sql
```

These queries analyze population trends, cross-source differences, and year-over-year population growth.

## 13. Open the Power BI Dashboard

Open:

`dashboards/Vietnam_Population_Dashboard.pbix`

The dashboard uses PostgreSQL as its data source.

Update the connection settings if your local PostgreSQL server or port differs from the development configuration, then refresh the data.

The report contains population KPIs, population trends, cross-source differences, growth analysis, and interactive slicers.

## 14. Expected Results

| Metric | Expected Result |
|---|---:|
| Data sources | 3 |
| Input files | 7 |
| Standardized records | 110 |
| Database observations | 110 |
| Years | 2015–2024 |
| Duplicate business keys | 0 |

## 15. Important Limitations

- UN and NSO require manual CSV preparation.
- UN 2024 uses a WPP2024 Medium variant projection.
- NSO reports annual average population, whereas UN population values use a July 1 reference date.
- Published population growth values can differ from year-over-year growth calculated from annual population counts.
- Data from different providers should not automatically be treated as independent or directly equivalent statistical observations.
