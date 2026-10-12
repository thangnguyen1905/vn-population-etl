# Population Data Sources

## Scope

- Country: Viet Nam (VNM)
- Years: 2015–2024
- Indicators: Total population, male population, female population, population growth

## 1. World Bank

- Provider: World Bank
- Dataset: World Development Indicators
- Format: JSON
- Extraction: REST API using Python Requests
- Country: VNM
- Years: 2015–2024
- Indicators:
  - SP.POP.TOTL
  - SP.POP.TOTL.MA.IN
  - SP.POP.TOTL.FE.IN
  - SP.POP.GROW

## 2. United Nations

- Provider: United Nations Population Division
- Dataset: World Population Prospects 2024
- Original format: Excel
- Current input format: CSV
- Country: Viet Nam (VNM)
- Estimates: 2015–2023
- Medium variant: 2024
- Original population unit: Thousand persons
- Preparation: Manually filtered Viet Nam records and removed unrelated indicator groups.
- Important: Medium variant 2024 is a projection in the WPP 2024 release.

## 3. Vietnam NSO

- Provider: National Statistics Office of Vietnam
- Dataset: V02.02 — Average population by sex and urban/rural residence
- Format: CSV exported from PX-Web
- Years: 2015–2024
- Original unit: Thousand persons
- Categories: Total, Male, Female
- Preparation: Manually exported and simplified the CSV header.
- Important: Verify statistical definitions and data status before cross-source comparison.

## Notes

The UN and NSO CSV files are manually prepared inputs, not automated website downloads.

The Extract pipeline preserves these files without modifying their contents. Data cleaning, unit conversion and cross-source comparison belong to later stages.