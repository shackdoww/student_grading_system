-- Additive and repeatable; existing school records are retained.
ALTER TABLE students ADD COLUMN IF NOT EXISTS year_level INTEGER;
ALTER TABLE students ALTER COLUMN email DROP NOT NULL;
ALTER TABLE teachers ALTER COLUMN email DROP NOT NULL;
UPDATE students SET email=NULL WHERE btrim(email)='';
UPDATE teachers SET email=NULL WHERE btrim(email)='';
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='students_year_level_check' AND conrelid='students'::regclass) THEN
        ALTER TABLE students ADD CONSTRAINT students_year_level_check CHECK (year_level BETWEEN 1 AND 6);
    END IF;
END $$;

ALTER TABLE grading_periods ADD COLUMN IF NOT EXISTS period_order INTEGER;
WITH ordered AS (
    SELECT period_id, row_number() OVER (PARTITION BY school_year, semester ORDER BY start_date, period_id) AS position
    FROM grading_periods
) UPDATE grading_periods p SET period_order=o.position FROM ordered o
  WHERE p.period_id=o.period_id AND p.period_order IS NULL;
ALTER TABLE grading_periods ALTER COLUMN period_order SET DEFAULT 1;
ALTER TABLE grading_periods ALTER COLUMN period_order SET NOT NULL;

ALTER TABLE period_grade_results ADD COLUMN IF NOT EXISTS midterm_equiv NUMERIC(3,2);
ALTER TABLE period_grade_results ADD COLUMN IF NOT EXISTS finals_equiv NUMERIC(3,2);
ALTER TABLE period_grade_results ADD COLUMN IF NOT EXISTS final_equiv NUMERIC(3,2);
ALTER TABLE period_grade_results ADD COLUMN IF NOT EXISTS remarks TEXT;

CREATE TABLE IF NOT EXISTS grade_audit_log (
    log_id BIGSERIAL PRIMARY KEY,
    table_name TEXT NOT NULL,
    record_id TEXT NOT NULL,
    action TEXT NOT NULL,
    old_value JSONB,
    new_value JSONB,
    changed_by TEXT NOT NULL,
    changed_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE OR REPLACE FUNCTION audit_grade_change() RETURNS TRIGGER AS $$
DECLARE old_row JSONB; new_row JSONB; identity_row JSONB;
BEGIN
    IF TG_OP <> 'INSERT' THEN old_row=to_jsonb(OLD); END IF;
    IF TG_OP <> 'DELETE' THEN new_row=to_jsonb(NEW); END IF;
    IF TG_OP='UPDATE' AND old_row=new_row THEN RETURN NEW; END IF;
    identity_row=COALESCE(new_row,old_row);
    INSERT INTO grade_audit_log(table_name,record_id,action,old_value,new_value,changed_by)
    VALUES (TG_TABLE_NAME,
        COALESCE(identity_row->>'score_id',identity_row->>'grade_id',
                 identity_row->>'enrollment_id',identity_row->>'percentage_id',identity_row->>'offering_id'),
        TG_OP, old_row, new_row, COALESCE(NULLIF(current_setting('app.actor',true),''),current_user));
    RETURN COALESCE(NEW,OLD);
END $$ LANGUAGE plpgsql;

DO $$ DECLARE target TEXT; BEGIN
    FOREACH target IN ARRAY ARRAY['grade_component_scores','grades','grade_percentages',
                                  'grading_policies','period_category_weights','period_grade_results'] LOOP
        EXECUTE format('DROP TRIGGER IF EXISTS trg_grade_audit ON %I', target);
        EXECUTE format('CREATE TRIGGER trg_grade_audit AFTER INSERT OR UPDATE OR DELETE ON %I FOR EACH ROW EXECUTE FUNCTION audit_grade_change()', target);
    END LOOP;
END $$;

-- Cross-class score protection also applies to direct SQL and CSV imports.
CREATE OR REPLACE FUNCTION validate_score_class() RETURNS TRIGGER AS $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM enrollments e JOIN grade_components c ON c.component_id=NEW.component_id
        JOIN grade_percentages p ON p.percentage_id=c.percentage_id
        WHERE e.enrollment_id=NEW.enrollment_id AND e.offering_id=p.offering_id
    ) THEN RAISE EXCEPTION 'Score component must belong to the enrolled class.'; END IF;
    RETURN NEW;
END $$ LANGUAGE plpgsql;
DROP TRIGGER IF EXISTS trg_score_class ON grade_component_scores;
CREATE TRIGGER trg_score_class BEFORE INSERT OR UPDATE ON grade_component_scores
FOR EACH ROW EXECUTE FUNCTION validate_score_class();
