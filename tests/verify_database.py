from app.calculator.grade_calculator import GradeCalculator
from app.database.connection import get_connection
from app.repositories.score_repository import ScoreRepository


def main():
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM students WHERE student_id = 'S001'")
            student_exists = cursor.fetchone()[0] == 1

            cursor.execute("SELECT COUNT(*) FROM enrollments WHERE enrollment_id = 'E001'")
            enrollment_exists = cursor.fetchone()[0] == 1

            cursor.execute(
                "SELECT COUNT(*) FROM grade_component_scores WHERE enrollment_id = 'E001'"
            )
            score_count = cursor.fetchone()[0]

    print(f"S001 exists: {student_exists}")
    print(f"E001 exists: {enrollment_exists}")
    print(f"E001 score count: {score_count}")

    if not student_exists or not enrollment_exists or score_count == 0:
        raise SystemExit("Database verification failed: expected sample data is missing.")

    scores = ScoreRepository().find_by_enrollment_id("E001")
    result = GradeCalculator().calculate_breakdown(scores)

    print(f"Calculated final grade: {result['final_grade']:.2f}%")
    print(f"Total grading weight: {result['total_weight']:.2f}%")

    if result["final_grade"] != 86.10:
        raise SystemExit(
            f"Database verification failed: expected 86.10%, got {result['final_grade']:.2f}%."
        )

    print("Database integration verification passed.")


if __name__ == "__main__":
    main()
