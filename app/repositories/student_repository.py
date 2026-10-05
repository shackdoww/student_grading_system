from app.database.connection import get_connection


class StudentRepository:

    def find_all(self):
        connection = get_connection()
        cursor = connection.cursor()

        try:
            cursor.execute("""
                SELECT student_id, first_name, last_name, email, program, status
                FROM students
                ORDER BY last_name, first_name
            """)
            return cursor.fetchall()
        finally:
            cursor.close()
            connection.close()

    def find_by_id(self, student_id):
        connection = get_connection()
        cursor = connection.cursor()

        try:
            cursor.execute("""
                SELECT student_id, first_name, last_name, email, program, status
                FROM students
                WHERE student_id = %s
            """, (student_id,))
            return cursor.fetchone()
        finally:
            cursor.close()
            connection.close()

    def save(self, student_id, first_name, last_name, email, program, status):
        connection = get_connection()
        cursor = connection.cursor()

        try:
            cursor.execute("""
                INSERT INTO students (
                    student_id, first_name, last_name, email, program, status
                )
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (student_id)
                DO UPDATE SET
                    first_name = EXCLUDED.first_name,
                    last_name = EXCLUDED.last_name,
                    email = EXCLUDED.email,
                    program = EXCLUDED.program,
                    status = EXCLUDED.status
            """, (student_id, first_name, last_name, email, program, status))
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            cursor.close()
            connection.close()

    def save_many(self, students):
        connection = get_connection()
        cursor = connection.cursor()
        try:
            for student in students:
                cursor.execute("""
                    INSERT INTO students (
                        student_id, first_name, last_name, email, program, status
                    )
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (student_id)
                    DO UPDATE SET
                        first_name = EXCLUDED.first_name,
                        last_name = EXCLUDED.last_name,
                        email = EXCLUDED.email,
                        program = EXCLUDED.program,
                        status = EXCLUDED.status
                """, (
                    student["student_id"], student["first_name"], student["last_name"],
                    student["email"], student["program"], student["status"]
                ))
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            cursor.close()
            connection.close()

    def get_import_conflicts(self, student_ids, emails):
        connection = get_connection()
        cursor = connection.cursor()
        try:
            cursor.execute("""
                SELECT student_id, email
                FROM students
                WHERE student_id = ANY(%s) OR email = ANY(%s)
            """, (student_ids, emails))
            return cursor.fetchall()
        finally:
            cursor.close()
            connection.close()

    def delete(self, student_id):
        connection = get_connection()
        cursor = connection.cursor()

        try:
            cursor.execute(
                "DELETE FROM students WHERE student_id = %s",
                (student_id,)
            )
            deleted = cursor.rowcount > 0
            connection.commit()
            return deleted
        except Exception:
            connection.rollback()
            raise
        finally:
            cursor.close()
            connection.close()
