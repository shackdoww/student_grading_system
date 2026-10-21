-- Canonical CSPC 103 schema. Install with python -m app.database.apply_migration --all.
CREATE TABLE schema_version (version INTEGER PRIMARY KEY, installed_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP);
INSERT INTO schema_version(version) VALUES (5);

CREATE TABLE student (
    student_id VARCHAR(50) PRIMARY KEY CHECK (btrim(student_id)<>''),
    first_name VARCHAR(100) NOT NULL CHECK (btrim(first_name)<>''),
    last_name VARCHAR(100) NOT NULL CHECK (btrim(last_name)<>''),
    email VARCHAR(150) UNIQUE,
    program VARCHAR(100) NOT NULL CHECK (btrim(program)<>''),
    year_level INTEGER CHECK (year_level BETWEEN 1 AND 6),
    status VARCHAR(50) NOT NULL CHECK (btrim(status)<>'')
);
CREATE TABLE teacher (
    teacher_id VARCHAR(50) PRIMARY KEY CHECK (btrim(teacher_id)<>''),
    first_name VARCHAR(100) NOT NULL CHECK (btrim(first_name)<>''),
    last_name VARCHAR(100) NOT NULL CHECK (btrim(last_name)<>''),
    email VARCHAR(150) UNIQUE,
    department VARCHAR(100) NOT NULL CHECK (btrim(department)<>''),
    status VARCHAR(50) NOT NULL CHECK (btrim(status)<>'')
);
CREATE TABLE subject (
    subject_id VARCHAR(50) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    subject_code VARCHAR(50) UNIQUE NOT NULL CHECK (btrim(subject_code)<>''),
    subject_name VARCHAR(150) NOT NULL CHECK (btrim(subject_name)<>''),
    description TEXT,
    units INTEGER NOT NULL CHECK (units>0)
);
CREATE TABLE class (
    class_id VARCHAR(50) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    class_code VARCHAR(50) NOT NULL CHECK (btrim(class_code)<>''),
    subject_id VARCHAR(50) NOT NULL REFERENCES subject(subject_id),
    teacher_id VARCHAR(50) NOT NULL REFERENCES teacher(teacher_id),
    section VARCHAR(50) NOT NULL CHECK (btrim(section)<>''),
    school_year VARCHAR(20) NOT NULL CHECK (btrim(school_year)<>''),
    semester VARCHAR(50) NOT NULL CHECK (btrim(semester)<>''),
    schedule VARCHAR(150) NOT NULL CHECK (btrim(schedule)<>''),
    room VARCHAR(100)
);
CREATE TABLE enrollment (
    enrollment_id VARCHAR(50) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    student_id VARCHAR(50) NOT NULL REFERENCES student(student_id),
    class_id VARCHAR(50) NOT NULL REFERENCES class(class_id),
    enroll_date DATE NOT NULL DEFAULT CURRENT_DATE,
    status VARCHAR(50) NOT NULL CHECK (status IN ('Enrolled','Active','Dropped','Completed')),
    CONSTRAINT unique_student_class UNIQUE(student_id,class_id)
);
CREATE TABLE grading_period (
    period_id VARCHAR(50) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    name VARCHAR(100) NOT NULL CHECK (btrim(name)<>''),
    period_order INTEGER NOT NULL CHECK (period_order>0),
    start_date DATE NOT NULL,
    end_date DATE NOT NULL CHECK (end_date>=start_date),
    school_year VARCHAR(20) NOT NULL CHECK (btrim(school_year)<>''),
    semester VARCHAR(50) NOT NULL CHECK (btrim(semester)<>'')
);
CREATE TABLE grade_component (
    component_id VARCHAR(50) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    period_id VARCHAR(50) NOT NULL REFERENCES grading_period(period_id),
    name VARCHAR(150) NOT NULL CHECK (btrim(name)<>''),
    type VARCHAR(50) NOT NULL CHECK (btrim(type)<>''),
    max_score NUMERIC(10,2) NOT NULL CHECK (max_score>0 AND max_score<100000000),
    description TEXT
);
CREATE TABLE grade_percentage (
    percentage_id VARCHAR(50) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    class_id VARCHAR(50) NOT NULL REFERENCES class(class_id),
    component_id VARCHAR(50) NOT NULL REFERENCES grade_component(component_id),
    percentage NUMERIC(5,2) NOT NULL CHECK (percentage>0 AND percentage<=100),
    UNIQUE(class_id,component_id)
);
CREATE TABLE grade_component_score (
    score_id VARCHAR(50) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    enrollment_id VARCHAR(50) NOT NULL REFERENCES enrollment(enrollment_id),
    component_id VARCHAR(50) NOT NULL REFERENCES grade_component(component_id),
    score NUMERIC(10,2) NOT NULL CHECK (score>=0 AND score<100000000),
    remarks TEXT,
    date_recorded DATE NOT NULL DEFAULT CURRENT_DATE,
    UNIQUE(enrollment_id,component_id)
);
CREATE TABLE grading_policy (
    class_id VARCHAR(50) PRIMARY KEY REFERENCES class(class_id),
    midterm_period_id VARCHAR(50) NOT NULL REFERENCES grading_period(period_id),
    final_period_id VARCHAR(50) NOT NULL REFERENCES grading_period(period_id),
    midterm_weight NUMERIC(5,2) NOT NULL CHECK (midterm_weight>0 AND midterm_weight<100),
    final_weight NUMERIC(5,2) NOT NULL CHECK (final_weight>0 AND final_weight<100),
    CHECK (midterm_period_id<>final_period_id),
    CHECK (midterm_weight+final_weight=100)
);
CREATE TABLE grade (
    grade_id VARCHAR(50) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    enrollment_id VARCHAR(50) UNIQUE NOT NULL REFERENCES enrollment(enrollment_id),
    midterm_grade NUMERIC(5,2) CHECK (midterm_grade BETWEEN 0 AND 100),
    finals_grade NUMERIC(5,2) CHECK (finals_grade BETWEEN 0 AND 100),
    overall_grade NUMERIC(5,2) CHECK (overall_grade BETWEEN 0 AND 100),
    midterm_equiv NUMERIC(3,2) CHECK (midterm_equiv IN (1,1.25,1.5,1.75,2,2.25,2.5,2.75,3,5)),
    finals_equiv NUMERIC(3,2) CHECK (finals_equiv IN (1,1.25,1.5,1.75,2,2.25,2.5,2.75,3,5)),
    final_equiv NUMERIC(3,2) CHECK (final_equiv IN (1,1.25,1.5,1.75,2,2.25,2.5,2.75,3,5)),
    remarks TEXT CHECK (remarks IS NULL OR remarks IN ('Passed','Failed')),
    date_encoded DATE NOT NULL DEFAULT CURRENT_DATE,
    CHECK ((overall_grade IS NULL AND final_equiv IS NULL AND remarks IS NULL) OR
           (midterm_grade IS NOT NULL AND finals_grade IS NOT NULL AND overall_grade IS NOT NULL AND
            midterm_equiv IS NOT NULL AND finals_equiv IS NOT NULL AND final_equiv IS NOT NULL AND
            remarks=CASE WHEN final_equiv=5 THEN 'Failed' ELSE 'Passed' END))
);
CREATE TABLE audit_log (
    log_id BIGSERIAL PRIMARY KEY,
    table_name TEXT NOT NULL,
    record_id TEXT NOT NULL,
    action TEXT NOT NULL,
    old_value JSONB,
    new_value JSONB,
    changed_by TEXT NOT NULL,
    changed_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    source_reference TEXT
);
CREATE TABLE user_accounts (
    user_id UUID PRIMARY KEY,
    username VARCHAR(80) UNIQUE NOT NULL,
    full_name VARCHAR(160) NOT NULL,
    password_hash TEXT NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('admin','dean','teacher','registrar')),
    teacher_id VARCHAR(50) REFERENCES teacher(teacher_id),
    active BOOLEAN NOT NULL DEFAULT TRUE,
    failed_attempts INTEGER NOT NULL DEFAULT 0,
    locked_until TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK ((role='teacher' AND teacher_id IS NOT NULL) OR (role<>'teacher' AND teacher_id IS NULL))
);
CREATE TABLE account_sessions (
    token_hash VARCHAR(64) PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES user_accounts(user_id),
    expires_at TIMESTAMPTZ NOT NULL
);
CREATE TABLE security_events (
    event_id BIGSERIAL PRIMARY KEY,
    actor_id UUID REFERENCES user_accounts(user_id),
    action VARCHAR(80) NOT NULL,
    target TEXT NOT NULL,
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX enrollment_student_idx ON enrollment(student_id);
CREATE INDEX enrollment_class_idx ON enrollment(class_id);
CREATE INDEX class_teacher_idx ON class(teacher_id);
CREATE INDEX component_period_idx ON grade_component(period_id);
CREATE INDEX weight_component_idx ON grade_percentage(component_id);
CREATE INDEX score_component_idx ON grade_component_score(component_id);
CREATE INDEX audit_record_idx ON audit_log(table_name,record_id,changed_at);

CREATE FUNCTION record_provenance() RETURNS TRIGGER AS $$
DECLARE actor TEXT; source TEXT;
BEGIN
    actor=NULLIF(current_setting('app.actor',true),'');
    source=NULLIF(current_setting('app.source',true),'');
    IF TG_OP='UPDATE' THEN
        IF (to_jsonb(NEW)-ARRAY['set_by','created_by','updated_by','created_at','updated_at']) =
           (to_jsonb(OLD)-ARRAY['set_by','created_by','updated_by','created_at','updated_at']) THEN
            RETURN OLD;
        END IF;
        NEW.created_by=OLD.created_by; NEW.created_at=OLD.created_at;
        NEW.set_by=OLD.set_by;
    ELSE
        NEW.created_by=actor; NEW.created_at=CURRENT_TIMESTAMP;
        NEW.set_by=NULL;
    END IF;
    IF source IS NOT NULL AND NOT source=ANY(string_to_array(COALESCE(NEW.set_by,''),'; ')) THEN
        NEW.set_by=concat_ws('; ',NEW.set_by,source);
    END IF;
    NEW.updated_by=actor; NEW.updated_at=CURRENT_TIMESTAMP;
    RETURN NEW;
END $$ LANGUAGE plpgsql;
CREATE FUNCTION record_audit() RETURNS TRIGGER AS $$
DECLARE old_row JSONB; new_row JSONB; row_data JSONB;
BEGIN
    IF TG_OP<>'INSERT' THEN old_row=to_jsonb(OLD); END IF;
    IF TG_OP<>'DELETE' THEN new_row=to_jsonb(NEW); END IF;
    IF TG_OP='UPDATE' AND old_row=new_row THEN RETURN NEW; END IF;
    row_data=COALESCE(new_row,old_row);
    INSERT INTO audit_log(table_name,record_id,action,old_value,new_value,changed_by,source_reference)
    VALUES (upper(TG_TABLE_NAME),row_data->>TG_ARGV[0],TG_OP,old_row,new_row,
            COALESCE(NULLIF(current_setting('app.actor',true),''),current_user),NULLIF(current_setting('app.source',true),''));
    RETURN COALESCE(NEW,OLD);
END $$ LANGUAGE plpgsql;
DO $$ DECLARE pair TEXT[]; BEGIN
    FOREACH pair SLICE 1 IN ARRAY ARRAY[
        ['student','student_id'],['teacher','teacher_id'],['subject','subject_id'],['class','class_id'],
        ['enrollment','enrollment_id'],['grading_period','period_id'],['grade_component','component_id'],
        ['grade_percentage','percentage_id'],['grade_component_score','score_id'],['grade','grade_id'],['grading_policy','class_id']
    ] LOOP
        EXECUTE format('ALTER TABLE %I ADD COLUMN set_by TEXT, ADD COLUMN created_by TEXT, ADD COLUMN updated_by TEXT, ADD COLUMN created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP, ADD COLUMN updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP',pair[1]);
        EXECUTE format('CREATE TRIGGER provenance BEFORE INSERT OR UPDATE ON %I FOR EACH ROW EXECUTE FUNCTION record_provenance()',pair[1]);
        EXECUTE format('CREATE TRIGGER audit AFTER INSERT OR UPDATE OR DELETE ON %I FOR EACH ROW EXECUTE FUNCTION record_audit(%L)',pair[1],pair[2]);
    END LOOP;
END $$;

CREATE FUNCTION validate_recorded_score() RETURNS TRIGGER AS $$
DECLARE maximum NUMERIC; cid TEXT;
BEGIN
    SELECT max_score INTO maximum FROM grade_component WHERE component_id=NEW.component_id FOR SHARE;
    SELECT class_id INTO cid FROM enrollment WHERE enrollment_id=NEW.enrollment_id FOR SHARE;
    IF maximum IS NULL OR NEW.score<0 OR NEW.score>maximum THEN
        RAISE EXCEPTION 'Score must be between zero and component maximum.';
    END IF;
    IF NOT EXISTS(SELECT 1 FROM grade_percentage WHERE class_id=cid AND component_id=NEW.component_id) THEN
        RAISE EXCEPTION 'Score component must be assigned to the enrolled class.';
    END IF;
    RETURN NEW;
END $$ LANGUAGE plpgsql;
CREATE TRIGGER validate_score BEFORE INSERT OR UPDATE ON grade_component_score
FOR EACH ROW EXECUTE FUNCTION validate_recorded_score();

-- Deferred checks see the final state of an atomic configuration edit.
CREATE FUNCTION validate_configuration() RETURNS TRIGGER AS $$
BEGIN
    IF EXISTS(SELECT 1 FROM grade_percentage w JOIN grade_component c USING(component_id)
        GROUP BY w.class_id,c.period_id HAVING sum(w.percentage)<>100) THEN
        RAISE EXCEPTION 'Component weights must total 100%% in every configured class/period.';
    END IF;
    IF EXISTS(SELECT 1 FROM grade_percentage w JOIN grade_component gc USING(component_id)
        JOIN grading_period p ON p.period_id=gc.period_id JOIN class c ON c.class_id=w.class_id
        WHERE (p.school_year,p.semester)<>(c.school_year,c.semester)) THEN
        RAISE EXCEPTION 'Component periods must match the class term.';
    END IF;
    IF EXISTS(SELECT 1 FROM grading_policy g JOIN class c USING(class_id)
        JOIN grading_period m ON m.period_id=g.midterm_period_id JOIN grading_period f ON f.period_id=g.final_period_id
        WHERE (m.school_year,m.semester)<>(c.school_year,c.semester) OR (f.school_year,f.semester)<>(c.school_year,c.semester)) THEN
        RAISE EXCEPTION 'Policy periods must match the class term.';
    END IF;
    IF EXISTS(SELECT 1 FROM grading_policy p WHERE
        NOT EXISTS(SELECT 1 FROM grade_percentage w JOIN grade_component c USING(component_id) WHERE w.class_id=p.class_id AND c.period_id=p.midterm_period_id) OR
        NOT EXISTS(SELECT 1 FROM grade_percentage w JOIN grade_component c USING(component_id) WHERE w.class_id=p.class_id AND c.period_id=p.final_period_id) OR
        EXISTS(SELECT 1 FROM grade_percentage w JOIN grade_component c USING(component_id) WHERE w.class_id=p.class_id AND c.period_id NOT IN (p.midterm_period_id,p.final_period_id))) THEN
        RAISE EXCEPTION 'Policy requires exactly its selected periods and complete component weights.';
    END IF;
    IF EXISTS(SELECT 1 FROM grade_component_score s JOIN grade_component c USING(component_id)
        JOIN enrollment e USING(enrollment_id) WHERE s.score>c.max_score OR
        NOT EXISTS(SELECT 1 FROM grade_percentage w WHERE w.class_id=e.class_id AND w.component_id=s.component_id)) THEN
        RAISE EXCEPTION 'This change would invalidate recorded scores or class assignments.';
    END IF;
    RETURN NULL;
END $$ LANGUAGE plpgsql;
DO $$ DECLARE target TEXT; BEGIN
    FOREACH target IN ARRAY ARRAY['grade_percentage','grade_component','class','grading_period','grading_policy','enrollment'] LOOP
        EXECUTE format('CREATE CONSTRAINT TRIGGER valid_configuration AFTER INSERT OR UPDATE OR DELETE ON %I DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION validate_configuration()',target);
    END LOOP;
END $$;
