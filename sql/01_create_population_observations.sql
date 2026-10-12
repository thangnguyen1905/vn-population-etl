CREATE TABLE IF NOT EXISTS public.population_observations
(
    -- 1. Primary Key
    id BIGINT GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,

    -- 2. Observation identity
    country_code VARCHAR(3) NOT NULL,
    year SMALLINT NOT NULL,
    source VARCHAR(100) NOT NULL,
    dataset VARCHAR(100) NOT NULL,
    indicator VARCHAR(50) NOT NULL,

    -- 3. Statistical value
    value NUMERIC(24,12) NOT NULL,
    unit VARCHAR(20) NOT NULL,

    -- 4. Source metadata
    data_status VARCHAR(50) NOT NULL,
    variant VARCHAR(50) NOT NULL DEFAULT '',
    reference_period VARCHAR(50) NOT NULL,
    source_indicator TEXT NOT NULL,
    source_file TEXT NOT NULL,
    extract_run_id VARCHAR(50) NOT NULL,

    -- 5. Database metadata
    loaded_at TIMESTAMPTZ NOT NULL
        DEFAULT CURRENT_TIMESTAMP,

    updated_at TIMESTAMPTZ NOT NULL
        DEFAULT CURRENT_TIMESTAMP,

    -- 6. Business Unique Constraint
    CONSTRAINT uq_population_observation
        UNIQUE (
            country_code,
            source,
            dataset,
            variant,
            year,
            indicator
        ),

    -- 7. Country validation
    CONSTRAINT chk_country_code
        CHECK (country_code ~ '^[A-Z]{3}$'),

    -- 8. Year validation
    CONSTRAINT chk_year
        CHECK (year >= 1900),

    -- 9. Indicator, unit and value validation
    CONSTRAINT chk_indicator_unit_value
        CHECK (
            (
                indicator IN (
                    'total_population',
                    'male_population',
                    'female_population'
                )
                AND unit = 'persons'
                AND value >= 0
            )
            OR
            (
                indicator = 'population_growth_rate'
                AND unit = 'percent'
            )
        )
);