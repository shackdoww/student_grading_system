from app.repositories.enrollment_repository import EnrollmentRepository
from app.repositories.student_repository import StudentRepository
from app.services.grading_service import GradingService


student_repository = StudentRepository()
enrollment_repository = EnrollmentRepository()
grading_service = GradingService()


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
        print("1. Find Student")
        print("2. View Student Enrollments")
        print("3. Calculate and Save Grade")
        print("4. View Saved Grade")
        print("5. Exit")

        choice = input("Choose an option: ").strip()

        if choice == "1":
            student_id = input("Enter student ID: ").strip()
            try:
                print_student(student_repository.find_by_id(student_id))
            except Exception as error:
                print(f"Database error: {error}")

        elif choice == "2":
            student_id = input("Enter student ID: ").strip()
            try:
                show_enrollments(student_id)
            except Exception as error:
                print(f"Database error: {error}")

        elif choice == "3":
            calculate_grade()

        elif choice == "4":
            view_saved_grade()

        elif choice == "5":
            print("Goodbye.")
            break

        else:
            print("Invalid option. Please choose 1-5.")


if __name__ == "__main__":
    main()
