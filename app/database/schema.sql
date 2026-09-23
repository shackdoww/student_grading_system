-- ============================================
-- STUDENT INFORMATION AND GRADING SYSTEM
-- PostgreSQL Database Schema
-- ============================================

CREATE TABLE students (
                          student_id VARCHAR(50) PRIMARY KEY,
                          first_name VARCHAR(100) NOT NULL,
                          last_name VARCHAR(100) NOT NULL,
                          email VARCHAR(150) UNIQUE NOT NULL,
                          program VARCHAR(100) NOT NULL,
                          status VARCHAR(50) NOT NULL
);

CREATE TABLE teachers (
                          teacher_id VARCHAR(50) PRIMARY KEY,
                          first_name VARCHAR(100) NOT NULL,
                          last_name VARCHAR(100) NOT NULL,
                          email VARCHAR(150) UNIQUE NOT NULL,
                          department VARCHAR(100) NOT NULL,
                          status VARCHAR(50) NOT NULL
);

CREATE TABLE subjects (
                          subject_id VARCHAR(50) PRIMARY KEY,
                          subject_code VARCHAR(50) UNIQUE NOT NULL,
                          subject_name VARCHAR(150) NOT NULL,
                          description TEXT,
                          units INTEGER NOT NULL CHECK (units > 0)
);

CREATE TABLE grading_periods (
                                 period_id VARCHAR(50) PRIMARY KEY,
                                 name VARCHAR(100) NOT NULL,
                                 start_date DATE NOT NULL,
                                 end_date DATE NOT NULL,
                                 school_year VARCHAR(20) NOT NULL,
                                 semester VARCHAR(50) NOT NULL,
                                 CHECK (end_date >= start_date)
);

CREATE TABLE class_offerings (
                                 offering_id VARCHAR(50) PRIMARY KEY,
                                 class_code VARCHAR(50) NOT NULL,
                                 schedule VARCHAR(150) NOT NULL,
                                 section VARCHAR(50) NOT NULL,
                                 school_year VARCHAR(20) NOT NULL,
                                 semester VARCHAR(50) NOT NULL,
                                 room VARCHAR(100),
                                 teacher_id VARCHAR(50) NOT NULL,
                                 subject_id VARCHAR(50) NOT NULL,

                                 CONSTRAINT fk_class_offering_teacher
                                     FOREIGN KEY (teacher_id)
                                         REFERENCES teachers(teacher_id),

                                 CONSTRAINT fk_class_offering_subject
                                     FOREIGN KEY (subject_id)
                                         REFERENCES subjects(subject_id)
);

CREATE TABLE enrollments (
                             enrollment_id VARCHAR(50) PRIMARY KEY,
                             enroll_date DATE NOT NULL,
                             status VARCHAR(50) NOT NULL,
                             student_id VARCHAR(50) NOT NULL,
                             offering_id VARCHAR(50) NOT NULL,

                             CONSTRAINT fk_enrollment_student
                                 FOREIGN KEY (student_id)
                                     REFERENCES students(student_id)
                                     ON DELETE CASCADE,

                             CONSTRAINT fk_enrollment_offering
                                 FOREIGN KEY (offering_id)
                                     REFERENCES class_offerings(offering_id)
                                     ON DELETE CASCADE,

                             CONSTRAINT unique_student_offering
                                 UNIQUE (student_id, offering_id)
);

CREATE TABLE grade_percentages (
                                   percentage_id VARCHAR(50) PRIMARY KEY,
                                   percentage NUMERIC(5,2) NOT NULL,
                                   offering_id VARCHAR(50) NOT NULL,

                                   CONSTRAINT fk_grade_percentage_offering
                                       FOREIGN KEY (offering_id)
                                           REFERENCES class_offerings(offering_id)
                                           ON DELETE CASCADE,

                                   CHECK (percentage > 0 AND percentage <= 100)
);

CREATE TABLE grade_components (
                                  component_id VARCHAR(50) PRIMARY KEY,
                                  name VARCHAR(150) NOT NULL,
                                  type VARCHAR(50) NOT NULL,
                                  max_score NUMERIC(10,2) NOT NULL,
                                  description TEXT,
                                  period_id VARCHAR(50) NOT NULL,
                                  percentage_id VARCHAR(50) NOT NULL,

                                  CONSTRAINT fk_grade_component_period
                                      FOREIGN KEY (period_id)
                                          REFERENCES grading_periods(period_id)
                                          ON DELETE CASCADE,

                                  CONSTRAINT fk_grade_component_percentage
                                      FOREIGN KEY (percentage_id)
                                          REFERENCES grade_percentages(percentage_id)
                                          ON DELETE CASCADE,

                                  CHECK (max_score > 0)
);

CREATE TABLE grade_component_scores (
                                        score_id VARCHAR(50) PRIMARY KEY,
                                        score NUMERIC(10,2) NOT NULL,
                                        remarks TEXT,
                                        date_recorded DATE NOT NULL,
                                        enrollment_id VARCHAR(50) NOT NULL,
                                        component_id VARCHAR(50) NOT NULL,

                                        CONSTRAINT fk_score_enrollment
                                            FOREIGN KEY (enrollment_id)
                                                REFERENCES enrollments(enrollment_id)
                                                ON DELETE CASCADE,

                                        CONSTRAINT fk_score_component
                                            FOREIGN KEY (component_id)
                                                REFERENCES grade_components(component_id)
                                                ON DELETE CASCADE,

                                        CONSTRAINT unique_enrollment_component
                                            UNIQUE (enrollment_id, component_id),

                                        CHECK (score >= 0)
);

CREATE TABLE grades (
                        grade_id VARCHAR(50) PRIMARY KEY,
                        final_grade NUMERIC(5,2) NOT NULL,
                        remarks TEXT,
                        date_encoded DATE NOT NULL,
                        enrollment_id VARCHAR(50) UNIQUE NOT NULL,

                        CONSTRAINT fk_grade_enrollment
                            FOREIGN KEY (enrollment_id)
                                REFERENCES enrollments(enrollment_id)
                                ON DELETE CASCADE,

                        CHECK (final_grade >= 0)
);

-- ============================================
-- INDEXES
-- ============================================

CREATE INDEX idx_enrollments_student
    ON enrollments(student_id);

CREATE INDEX idx_enrollments_offering
    ON enrollments(offering_id);

CREATE INDEX idx_class_offerings_teacher
    ON class_offerings(teacher_id);

CREATE INDEX idx_class_offerings_subject
    ON class_offerings(subject_id);

CREATE INDEX idx_grade_components_period
    ON grade_components(period_id);

CREATE INDEX idx_grade_components_percentage
    ON grade_components(percentage_id);

CREATE INDEX idx_scores_enrollment
    ON grade_component_scores(enrollment_id);

CREATE INDEX idx_scores_component
    ON grade_component_scores(component_id);