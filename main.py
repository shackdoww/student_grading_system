from app.repositories.enrollment_repository import EnrollmentRepository
from app.repositories.grade_component_repository import GradeComponentRepository
from app.repositories.score_repository import ScoreRepository
from app.repositories.student_repository import StudentRepository
from app.services.grading_service import GradingService
from app.services.score_service import ScoreService


student_repository = StudentRepository()
enrollment_repository = EnrollmentRepository()
score_repository = ScoreRepository()
component_repository = GradeComponentRepository()
grading_service = GradingService()
score_service = ScoreService()


def print_student(student):
    if not student:
        print("Student not found.")
        return

    print("\nStudent Information")
    print("-------------------")
    print(f"ID:      {student[0]}")
    print(f"Name:    {student[1]} {student[2]}")
    print(f"Email:   {student[3]}")
    print(f"Program: {student[4]}")
    print(f"Status:  {student[5]}")


def list_students():
    students = student_repository.find_all()

    if not students:
        print("No students found.")
        return

    print("\nStudents")
    print("--------")

    for student in students:
        print(
            f"{student[0]} | {student[1]} {student[2]} | "
            f"{student[4]} | {student[5]}"
        )


def show_enrollments(student_id):
    enrollments = enrollment_repository.find_by_student_id(student_id)

    if not enrollments:
        print("No enrollments found.")
        return []

    print("\nEnrollments")
    print("-----------")

    for index, enrollment in enumerate(enrollments, start=1):
        print(
            f"{index}. {enrollment[11]} - {enrollment[12]} "
            f"({enrollment[5]}, {enrollment[6]})"
        )
        print(f"   Enrollment ID: {enrollment[0]}")
        print(f"   Teacher: {enrollment[14]} {enrollment[15]}")
        print(f"   Room: {enrollment[9] or 'Not assigned'}")
        print(f"   Status: {enrollment[2]}")

    return enrollments


def show_components():
    offering_id = input("Enter class offering ID: ").strip()

    try:
        components = component_repository.find_by_offering_id(offering_id)

        if not components:
            print("No grade components found.")
            return

        print("\nGrade Components")
        print("----------------")

        for component in components:
            print(
                f"{component[0]} | {component[1]} | {component[2]} | "
                f"Max: {float(component[3]):.2f} | "
                f"Weight: {float(component[8]):.2f}%"
            )
            print(f"   Period: {component[6]}")
            print(f"   Description: {component[4] or 'None'}")
    except Exception as error:
        print(f"Database error: {error}")


def show_scores():
    enrollment_id = input("Enter enrollment ID: ").strip()

    try:
        scores = score_service.get_scores(enrollment_id)

        if not scores:
            print("No scores found.")
            return

        print("\nGrade Component Scores")
        print("----------------------")

        for score in scores:
            print(
                f"{score[5]} | {float(score[1]):.2f}/{float(score[7]):.2f} | "
                f"{score[6]} | Weight: {float(score[10]):.2f}%"
            )
            print(f"   Component ID: {score[4]}")
            print(f"   Period: {score[12]}")
            print(f"   Remarks: {score[2] or 'None'}")
            print(f"   Recorded: {score[3]}")
    except Exception as error:
        print(f"Database error: {error}")


def record_score():
    print("\nRecord / Update Score")
    print("---------------------")

    score_id = input("Score ID: ").strip()
    enrollment_id = input("Enrollment ID: ").strip()
    component_id = input("Component ID: ").strip()
    score = input("Score: ").strip()
    remarks = input("Remarks (optional): ").strip()

    try:
        score_service.record_score(
            score_id=score_id,
            enrollment_id=enrollment_id,
            component_id=component_id,
            score=score,
            remarks=remarks
        )
        print("Score saved successfully.")
    except ValueError as error:
        print(f"Error: {error}")
    except Exception as error:
        print(f"Database error: {error}")


def calculate_grade():
    enrollment_id = input("Enter enrollment ID: ").strip()

    try:
        final_grade = grading_service.calculate_and_save_grade(enrollment_id)
        print(f"\nFinal Grade: {final_grade:.2f}")
        print("Grade saved successfully.")
    except ValueError as error:
        print(f"Error: {error}")
    except Exception as error:
        print(f"Database error: {error}")


def view_saved_grade():
    enrollment_id = input("Enter enrollment ID: ").strip()

    try:
        grade = grading_service.get_saved_grade(enrollment_id)

        if not grade:
            print("No saved grade found.")
            return

        print("\nSaved Grade")
        print("-----------")
        print(f"Grade ID:     {grade[0]}")
        print(f"Final Grade:  {float(grade[1]):.2f}")
        print(f"Remarks:      {grade[2] or 'None'}")
        print(f"Date Encoded: {grade[3]}")
        print(f"Enrollment:   {grade[4]}")
    except Exception as error:
        print(f"Database error: {error}")


def main():
    while True:
        print("\n================================")
        print(" Student Information and Grading")
        print("================================")
        print("1. List Students")
        print("2. Find Student")
        print("3. View Student Enrollments")
        print("4. View Grade Components")
        print("5. View Grade Component Scores")
        print("6. Record / Update Score")
        print("7. Calculate and Save Grade")
        print("8. View Saved Grade")
        print("9. Exit")

        choice = input("Choose an option: ").strip()

        try:
            if choice == "1":
                list_students()
            elif choice == "2":
                student_id = input("Enter student ID: ").strip()
                print_student(student_repository.find_by_id(student_id))
            elif choice == "3":
                student_id = input("Enter student ID: ").strip()
                show_enrollments(student_id)
            elif choice == "4":
                show_components()
            elif choice == "5":
                show_scores()
            elif choice == "6":
                record_score()
            elif choice == "7":
                calculate_grade()
            elif choice == "8":
                view_saved_grade()
            elif choice == "9":
                print("Goodbye.")
                break
            else:
                print("Invalid option. Please choose 1-9.")
        except Exception as error:
            print(f"Database error: {error}")


if __name__ == "__main__":
    main()
