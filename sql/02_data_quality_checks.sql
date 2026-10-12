
-- ===================================================
-- Vietnam Population ETL
-- Stage 6: Data Quality Checks
-- ===================================================


-- 1. DATA COMPLETENESS: Record counts by source
SELECT
    country_code,
    source,
    COUNT(*) AS total_records,
    COUNT(DISTINCT year) AS total_years,
    COUNT(DISTINCT indicator) AS total_indicators
FROM public.population_observations
GROUP BY country_code, source
ORDER BY source;


-- 2. DATA COMPLETENESS: Find missing observations
WITH expected_pairs (source, indicator) AS (
    VALUES
        ('World Bank', 'total_population'),
        ('World Bank', 'male_population'),
        ('World Bank', 'female_population'),
        ('World Bank', 'population_growth_rate'),

        ('United Nations', 'total_population'),
        ('United Nations', 'male_population'),
        ('United Nations', 'female_population'),
        ('United Nations', 'population_growth_rate'),

        ('Vietnam NSO', 'total_population'),
        ('Vietnam NSO', 'male_population'),
        ('Vietnam NSO', 'female_population')
),
expected AS (
    SELECT
        pair.source,
        y.year,
        pair.indicator
    FROM expected_pairs AS pair
    CROSS JOIN generate_series(2015, 2024) AS y(year)
)
SELECT
    e.source,
    e.year,
    e.indicator AS missing_indicator
FROM expected AS e
LEFT JOIN public.population_observations AS p
    ON p.country_code = 'VNM'
    AND p.source = e.source
    AND p.year = e.year
    AND p.indicator = e.indicator
WHERE p.id IS NULL
ORDER BY e.source, e.year, e.indicator;


-- 3. DATA UNIQUENESS: Detect duplicate observations
SELECT
    country_code,
    source,
    year,
    indicator,
    COUNT(*) AS duplicate_count
FROM public.population_observations
GROUP BY
    country_code,
    source,
    year,
    indicator
HAVING COUNT(*) > 1;


-- 4. DATA VALIDITY: Invalid values or units
SELECT
    id,
    source,
    year,
    indicator,
    value,
    unit
FROM public.population_observations
WHERE
    (
        indicator IN (
            'total_population',
            'male_population',
            'female_population'
        )
        AND (value < 0 OR unit <> 'persons')
    )
    OR
    (
        indicator = 'population_growth_rate'
        AND unit <> 'percent'
    )
    OR indicator NOT IN (
        'total_population',
        'male_population',
        'female_population',
        'population_growth_rate'
    );


-- 5. DATA CONSISTENCY: Total vs Male + Female
WITH population_by_year AS (
    SELECT
        source,
        year,

        MAX(value) FILTER (
            WHERE indicator = 'total_population'
        ) AS total_pop,

        MAX(value) FILTER (
            WHERE indicator = 'male_population'
        ) AS male_pop,

        MAX(value) FILTER (
            WHERE indicator = 'female_population'
        ) AS female_pop

    FROM public.population_observations
    WHERE country_code = 'VNM'
    GROUP BY source, year
),
with_tolerance AS (
    SELECT
        *,
        CASE source
            WHEN 'World Bank' THEN 1
            WHEN 'United Nations' THEN 1000
            WHEN 'Vietnam NSO' THEN 100
            ELSE 0
        END AS tolerance_persons
    FROM population_by_year
)
SELECT
    source,
    COUNT(*) AS checked_years,

    MAX(
        ABS(total_pop - male_pop - female_pop)
    ) AS max_difference_persons,

    MAX(tolerance_persons) AS tolerance_persons,

    CASE
        WHEN COUNT(*) = 10
         AND COUNT(*) FILTER (
             WHERE total_pop IS NULL
                OR male_pop IS NULL
                OR female_pop IS NULL
         ) = 0
         AND MAX(
             ABS(total_pop - male_pop - female_pop)
         ) <= MAX(tolerance_persons)
        THEN 'PASS'
        ELSE 'FAIL'
    END AS quality_status

FROM with_tolerance
GROUP BY source
ORDER BY source;
