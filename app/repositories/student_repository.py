from app.database.connection import get_connection


class StudentRepository:

    def find_all(self):
        connection = get_connection()
        cursor = connection.cursor()

        try:
            cursor.execute("""
                SELECT student_id, first_name, last_name, email, program, status, year_level
                FROM student
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
                SELECT student_id, first_name, last_name, email, program, status, year_level
                FROM student
                WHERE student_id = %s
            """, (student_id,))
            return cursor.fetchone()
        finally:
            cursor.close()
            connection.close()

    def create(self, student_id, first_name, last_name, email, program, status, year_level=1):
        with get_connection() as connection:
            connection.execute('''INSERT INTO student
                (student_id,first_name,last_name,email,program,status,year_level)
                VALUES (%s,%s,%s,%s,%s,%s,%s)''',
                (student_id,first_name,last_name,email or None,program,status,year_level))

    def save(self, student_id, first_name, last_name, email, program, status, year_level=1):
        connection = get_connection()
        cursor = connection.cursor()

        try:
            cursor.execute("""
                INSERT INTO student (
                    student_id, first_name, last_name, email, program, status, year_level
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (student_id)
                DO UPDATE SET
                    first_name = EXCLUDED.first_name,
                    last_name = EXCLUDED.last_name,
                    email = EXCLUDED.email,
                    program = EXCLUDED.program,
                    status = EXCLUDED.status,
                    year_level = EXCLUDED.year_level
            """, (student_id, first_name, last_name, email or None, program, status, year_level))
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            cursor.close()
            connection.close()
