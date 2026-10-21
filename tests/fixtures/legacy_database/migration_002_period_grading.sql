-- Additive and repeatable. Existing scores, weights and consolidated grades
-- are intentionally not converted or overwritten.
CREATE TABLE IF NOT EXISTS grading_policies (
    offering_id VARCHAR(50) PRIMARY KEY REFERENCES class_offerings(offering_id),
    midterm_period_id VARCHAR(50) NOT NULL REFERENCES grading_periods(period_id),
    final_period_id VARCHAR(50) NOT NULL REFERENCES grading_periods(period_id),
    midterm_weight NUMERIC(5,2) NOT NULL CHECK (midterm_weight > 0),
    final_weight NUMERIC(5,2) NOT NULL CHECK (final_weight > 0),
    CHECK (midterm_period_id <> final_period_id),
    CHECK (midterm_weight + final_weight = 100)
);

CREATE TABLE IF NOT EXISTS period_category_weights (
    offering_id VARCHAR(50) NOT NULL REFERENCES grading_policies(offering_id),
    period_id VARCHAR(50) NOT NULL REFERENCES grading_periods(period_id),
    percentage_id VARCHAR(50) NOT NULL REFERENCES grade_percentages(percentage_id),
    weight NUMERIC(5,2) NOT NULL CHECK (weight > 0 AND weight <= 100),
    PRIMARY KEY (offering_id, period_id, percentage_id)
);

CREATE TABLE IF NOT EXISTS period_grade_results (
    enrollment_id VARCHAR(50) PRIMARY KEY REFERENCES enrollments(enrollment_id),
    midterm_grade NUMERIC(5,2) NOT NULL CHECK (midterm_grade BETWEEN 0 AND 100),
    final_grade NUMERIC(5,2) NOT NULL CHECK (final_grade BETWEEN 0 AND 100),
    overall_grade NUMERIC(5,2) NOT NULL CHECK (overall_grade BETWEEN 0 AND 100),
    calculated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
