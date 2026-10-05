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

Import order:
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

The data respects the schema foreign keys and score limits. Students use S101-S130 so the dataset does not conflict with the existing S001 sample student.

The application currently provides the CSV import workflow for students. The other CSVs form the complete relational test dataset for the corresponding Academic, Enrollment, Class Grades, and Report features.
