# School Test Dataset

A realistic relational dataset for school year 2026-2027.

Records:
- 30 students (S101-S130)
- 8 teachers
- 12 subjects
- 2 grading periods
- 12 class offerings
- 36 grading percentages
- 72 grade components
- 60 enrollments
- 360 component scores
- 60 final grades

Import order used by the application:
1. school_students.csv
2. school_teachers.csv
3. school_subjects.csv
4. school_grading_periods.csv
5. school_class_offerings.csv
6. school_grade_percentages.csv
7. school_grade_components.csv
8. school_enrollments.csv
9. school_grade_component_scores.csv
10. school_grades.csv

## In-app import

Use **Data Import** in the application's sidebar.

1. Click **SELECT DATASET FOLDER**.
2. Select this `test_data` folder.
3. Click **VALIDATE DATA**.
4. Review the validation result.
5. Click **IMPORT ENTIRE SCHOOL DATASET**.

The importer validates all ten files before writing anything. The database writes occur in foreign-key order inside one PostgreSQL transaction. If any insert/update fails, the entire transaction is rolled back.

Records with an existing primary key are updated, which makes the school dataset import repeatable. Unique-key conflicts involving a different existing record are rejected during validation.

The data uses S101-S130 for students so it does not conflict with the original S001 sample student.