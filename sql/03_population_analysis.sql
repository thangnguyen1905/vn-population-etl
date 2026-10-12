-- ============================================
-- 1. POPULATION TREND BY SOURCE (2015-2024)
-- ============================================

SELECT
    year,
    source,
    value AS total_population,
    unit,
    data_status,
    reference_period
FROM public.population_observations
WHERE country_code = 'VNM'
  AND indicator = 'total_population'
  AND year BETWEEN 2015 AND 2024
ORDER BY year, source;

-- ============================================
-- 2. CROSS-SOURCE POPULATION COMPARISON
-- ============================================

WITH population_comparison AS (
    SELECT
        year,

        MAX(value) FILTER (
            WHERE source = 'World Bank'
        ) AS wb_population,

        MAX(value) FILTER (
            WHERE source = 'United Nations'
        ) AS un_population,

        MAX(value) FILTER (
            WHERE source = 'Vietnam NSO'
        ) AS nso_population,

        MAX(data_status) FILTER (
            WHERE source = 'United Nations'
        ) AS un_data_status

    FROM public.population_observations

    WHERE country_code = 'VNM'
      AND indicator = 'total_population'

    GROUP BY year
)

SELECT
    year,

    wb_population,
    un_population,
    nso_population,

    -- UN compared with World Bank (persons)
    un_population - wb_population
        AS un_minus_wb,

    -- NSO compared with World Bank (persons)
    nso_population - wb_population
        AS nso_minus_wb,

    -- Percentage difference relative to World Bank
    ROUND(
        (nso_population - wb_population)
        / NULLIF(wb_population, 0) * 100,
        3
    ) AS nso_vs_wb_percent,

    un_data_status

FROM population_comparison

ORDER BY year;

-- ============================================
-- 3. YEAR-OVER-YEAR POPULATION GROWTH
-- ============================================

WITH population_trend AS (
    SELECT
        source,
        year,
        value AS current_population,

        LAG(value) OVER (
            PARTITION BY source
            ORDER BY year
        ) AS previous_population,

        data_status

    FROM public.population_observations

    WHERE country_code = 'VNM'
      AND indicator = 'total_population'
)

SELECT
    source,
    year,

    current_population,
    previous_population,

    -- Population change in persons
    current_population - previous_population
        AS population_change,

    -- Calculated year-over-year percentage
    ROUND(
        (current_population - previous_population)
        / NULLIF(previous_population, 0) * 100,
        3
    ) AS calculated_yoy_percent,

    data_status

FROM population_trend

ORDER BY source, year;