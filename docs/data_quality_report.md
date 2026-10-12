# Vietnam Population — Data Quality & Analysis Report

## 1. Overview

**Project:** Vietnam Population Data Integration & ETL Pipeline  
**Period:** 2015–2024  
**Country:** Viet Nam (VNM)  
**Sources:** World Bank, United Nations WPP2024, Vietnam NSO  
**Database:** PostgreSQL 17

The ETL pipeline successfully extracted, transformed, and loaded 110 standardized observations into PostgreSQL.

## 2. Data Quality Results

| Quality Dimension | Result | Status |
|---|---|---|
| Completeness | 110 observations across 3 sources | PASS |
| Expected year/indicator coverage | No missing observations | PASS |
| Uniqueness | No duplicate business keys | PASS |
| Validity | No invalid indicators, units, or negative population values | PASS |
| Population consistency | All three sources within configured tolerances | PASS |

Maximum differences between reported total population and the sum of male and female populations:

| Source | Maximum Difference |
|---|---:|
| World Bank | 0 persons |
| United Nations | 1,000 persons |
| Vietnam NSO | 60 persons |

These validation tolerances are project-specific technical rules, not official statistical standards.

## 3. Key Analytical Findings

### Population Trend

All three sources indicate that Viet Nam's population increased between 2015 and 2024.

World Bank population increased from 92,823,254 to 100,987,686 persons, while Vietnam NSO population increased from 92,228,600 to 101,343,750 persons.

### Cross-Source Comparison

World Bank and UN population figures are extremely close, with a maximum absolute difference of 345 persons across the analyzed years. Their underlying statistical data sources and methodologies should be investigated before treating them as independent estimates.

Vietnam NSO figures differ more noticeably from World Bank figures.

In 2017, NSO reported 890,977 fewer persons than World Bank. By 2023, the difference had narrowed to 42,982 fewer persons.

In 2024, NSO reported 356,064 more persons than World Bank, corresponding to approximately 0.353% relative to the World Bank value.

### Population Growth

Calculated year-over-year population growth for World Bank declined from approximately 1.268% in 2016 to 0.633% in 2024.

The corresponding UN values declined from approximately 1.268% to 0.634%.

NSO year-over-year growth was approximately 1.031% in 2024.

## 4. Data Interpretation Limitations

The sources are not automatically equivalent statistical measurements.

UN population figures refer to July 1. The 2024 UN value comes from the WPP2024 Medium variant projection, whereas 2015–2023 values come from the Estimates dataset.

Vietnam NSO reports annual average population figures. The prepared NSO CSV does not fully preserve each year's official statistical status.

World Bank indicator definitions and their underlying sources require further documentation.

Calculated year-over-year growth rates may differ from published population growth indicators due to methodology and reference-period differences.

Therefore, cross-source differences should not automatically be interpreted as errors.

## 5. SQL Artifacts

- `sql/02_data_quality_checks.sql` — Completeness, uniqueness, validity, and consistency checks.
- `sql/03_population_analysis.sql` — Population trends, cross-source comparison, and year-over-year growth.

## 6. Conclusion

The dataset passed all configured technical quality checks, and the analyses identified meaningful differences between statistical sources.

The standardized PostgreSQL dataset is ready for visualization, with appropriate source attribution and data-status context.