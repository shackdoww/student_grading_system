-- Apply this migration to an EXISTING student_grading_system database.
-- It does not drop tables or delete existing data.
-- Run once in PostgreSQL after the original schema has been created.

CREATE OR REPLACE FUNCTION validate_grade_component_score()
RETURNS TRIGGER AS $$
DECLARE
    maximum NUMERIC(10,2);
BEGIN
    SELECT max_score INTO maximum
    FROM grade_components
    WHERE component_id = NEW.component_id;

    IF maximum IS NULL THEN
        RAISE EXCEPTION 'Grade component % does not exist.', NEW.component_id;
    END IF;

    IF NEW.score < 0 OR NEW.score > maximum THEN
        RAISE EXCEPTION
            'Score % is outside the valid range 0-% for component %.',
            NEW.score, maximum, NEW.component_id;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_validate_grade_component_score
ON grade_component_scores;

CREATE TRIGGER trg_validate_grade_component_score
BEFORE INSERT OR UPDATE ON grade_component_scores
FOR EACH ROW
EXECUTE FUNCTION validate_grade_component_score();

CREATE OR REPLACE FUNCTION validate_grade_percentage_total()
RETURNS TRIGGER AS $$
DECLARE
    total NUMERIC(7,2);
BEGIN
    SELECT COALESCE(SUM(percentage), 0)
    INTO total
    FROM grade_percentages
    WHERE offering_id = NEW.offering_id
      AND percentage_id <> NEW.percentage_id;

    IF total + NEW.percentage > 100 THEN
        RAISE EXCEPTION
            'Total grading percentage for offering % cannot exceed 100%%.',
            NEW.offering_id;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_validate_grade_percentage_total
ON grade_percentages;

CREATE TRIGGER trg_validate_grade_percentage_total
BEFORE INSERT OR UPDATE ON grade_percentages
FOR EACH ROW
EXECUTE FUNCTION validate_grade_percentage_total();

-- Verify existing data before relying on the new validation.
DO $$
DECLARE
    invalid_score_count INTEGER;
    invalid_weight_count INTEGER;
BEGIN
    SELECT COUNT(*)
    INTO invalid_score_count
    FROM grade_component_scores gcs
    JOIN grade_components gc ON gcs.component_id = gc.component_id
    WHERE gcs.score < 0 OR gcs.score > gc.max_score;

    IF invalid_score_count > 0 THEN
        RAISE WARNING
            '% existing score(s) exceed their component maximum.',
            invalid_score_count;
    END IF;

    SELECT COUNT(*)
    INTO invalid_weight_count
    FROM (
        SELECT offering_id
        FROM grade_percentages
        GROUP BY offering_id
        HAVING SUM(percentage) > 100
    ) invalid;

    IF invalid_weight_count > 0 THEN
        RAISE WARNING
            '% offering(s) have grading percentages above 100%%.',
            invalid_weight_count;
    END IF;
END $$;
