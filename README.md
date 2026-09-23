# Student Information and Grading System

A Python and PostgreSQL student information and grading system based on the project's UML design.

## Technologies

- Python 3
- PostgreSQL
- psycopg
- python-dotenv
- IntelliJ IDEA
- Git and GitHub

## Project Structure

```
app/
├── calculator/
│   └── grade_calculator.py
├── database/
│   ├── connection.py
│   └── schema.sql
├── repositories/
│   ├── enrollment_repository.py
│   ├── grade_repository.py
│   ├── score_repository.py
│   └── student_repository.py
└── services/
    └── grading_service.py

main.py
requirements.txt
```

## Setup

1. Create the PostgreSQL database named `student_grading_system`.
2. Run `app/database/schema.sql`.
3. Create a local `.env` file:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=student_grading_system
DB_USER=postgres
DB_PASSWORD=your_actual_password
```

4. Install dependencies:

```bash
pip install -r requirements.txt
```

5. Run:

```bash
python main.py
```

## Grading Flow

```
Student
   ↓
Enrollment
   ↓
Grade Component Scores
   ↓
GradeCalculator
   ↓
GradingService
   ↓
GradeRepository
   ↓
grades table
```

The calculator converts each component score to a percentage, averages components that belong to the same grading percentage, applies the category weight, and adds the weighted results to produce the final grade.
