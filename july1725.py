"""
Write a Python script to create an SQLite database named students.db and a table students with columns id, name, and age.

Write a function to insert a list of student records into the students table.

Write a program to retrieve and print all rows from the students table.

Fetch all students from the students table who are older than 20.

Write a script to update a student's name given their ID.

Delete a student record based on their name.

Write a Python program that retrieves all students whose names start with the letter A using the LIKE operator.

Modify the insert function to use parameterized queries using ? placeholders to avoid SQL injection.

Count the number of students in each age group using GROUP BY.

Write a script to insert multiple student records into the database using executemany().

Write a function that takes a page number and limit, and returns paginated student results from the database.

Create a new table courses with course_id, course_name, and student_id, and write a query to fetch student names along with their enrolled course names using JOIN.

Write a script to create an index on the age column of the students table and explain how it improves performance.

Write Python code to export all student data from the students table to a CSV file named students.csv.

Write a function to check if a table named students exists in the database before querying it.
"""

import os
import sqlite3 as sq
import csv

def create_students_database(student_db):
    conn = sq.connect(student_db)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            age INTEGER NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def insert_students(db_file, student_name, student_age):
    conn = sq.connect(db_file)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO {} (name, age) VALUES (?, ?)'.format(os.path.basename(db_file).split(".")[0]), (student_name, student_age))
    conn.commit()
    conn.close()

def print_rows(db_file, rows = 'all'):
    conn = sq.connect(db_file)
    cursor = conn.cursor()
    if rows.strip().lower() == 'all':
        cursor.execute(f'SELECT * FROM {os.path.basename(db_file).split(".")[0]}')
        rows = cursor.fetchall()
    else:
        rows = rows.split(',')
        cursor.execute(f'SELECT * FROM {os.path.basename(db_file).split(".")[0]} WHERE id IN ({",".join("?" for _ in rows)})', rows)
    for row in rows:
        print(row)
    conn.close()

def get_students_older_than(db_file, age):
    conn = sq.connect(db_file)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM {} WHERE age > ?'.format(os.path.basename(db_file).split(".")[0]), (age,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def update_student_name(db_file, student_id, new_name):
    conn = sq.connect(db_file)
    cursor = conn.cursor()
    cursor.execute('UPDATE {} SET name = ? WHERE id = ?'.format(os.path.basename(db_file).split(".")[0]), (new_name, student_id))
    conn.commit()
    conn.close()

def delete_student_by_name(db_file, student_name):
    conn = sq.connect(db_file)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM {} WHERE name = ?'.format(os.path.basename(db_file).split(".")[0]), (student_name,))
    conn.commit()
    conn.close()

def get_students_starting_with_a(db_file):
    conn = sq.connect(db_file)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM {} WHERE name LIKE ?'.format(os.path.basename(db_file).split(".")[0]), ('A%',))
    rows = cursor.fetchall()
    conn.close()
    return rows

def count_students_by_age_group(db_file):
    conn = sq.connect(db_file)
    cursor = conn.cursor()
    cursor.execute('SELECT age, COUNT(*) FROM {} GROUP BY age'.format(os.path.basename(db_file).split(".")[0]))
    rows = cursor.fetchall()
    conn.close()
    return rows

def insert_multiple_students(db_file, students):
    conn = sq.connect(db_file)
    cursor = conn.cursor()
    cursor.executemany('INSERT INTO {} (name, age) VALUES (?, ?)'.format(os.path.basename(db_file).split(".")[0]), students)
    conn.commit()
    conn.close()

def get_paginated_students(db_file, page, limit):
    conn = sq.connect(db_file)
    cursor = conn.cursor()
    offset = (page - 1) * limit
    cursor.execute('SELECT * FROM {} LIMIT ? OFFSET ?'.format(os.path.basename(db_file).split(".")[0]), (limit, offset))
    rows = cursor.fetchall()
    conn.close()
    return rows

def create_courses_table():
    conn = sq.connect('courses.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS courses (
            course_id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_name TEXT NOT NULL,
            student_id INTEGER,
            FOREIGN KEY (student_id) REFERENCES students(id)
        )
    ''')
    conn.commit()
    conn.close()

def fetch_students_with_courses(db_file):
    conn = sq.connect(db_file)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT students.name, courses.course_name
        FROM students
        JOIN courses ON students.id = courses.student_id
    ''')
    rows = cursor.fetchall()
    conn.close()
    return rows

def create_index_on_age(db_file):
    conn = sq.connect(db_file)
    cursor = conn.cursor()
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_age ON students(age)')
    conn.commit()
    conn.close()

def export_students_to_csv(db_file, csv_file):
    conn = sq.connect(db_file)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM {}'.format(os.path.basename(db_file).split(".")[0]))
    rows = cursor.fetchall()
    with open(csv_file, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([description[0] for description in cursor.description])  # Write headers
        writer.writerows(rows)
    conn.close()

def check_table_exists(db_file, table_name):
    conn = sq.connect(db_file)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
    exists = cursor.fetchone() is not None
    conn.close()
    return exists
    
if __name__ == "__main__":
    student_db = 'students.db'
    create_students_database(student_db)
    insert_students(student_db, 'Alice', 22)
    insert_students(student_db, 'Bob', 19)
    insert_students(student_db, 'Charlie', 23)

    print("All students:")
    print_rows(student_db)

    print("\nStudents older than 20:")
    for student in get_students_older_than(student_db, 20):
        print(student)

    update_student_name(student_db, 1, 'Alicia')
    print("\nAfter updating Alice's name:")
    print_rows(student_db)

    delete_student_by_name(student_db, 'Bob')
    print("\nAfter deleting Bob:")
    print_rows(student_db)
    
    print("\nStudents whose names start with 'A':")
    for student in get_students_starting_with_a(student_db):
        print(student)
    
    print("\nCount of students by age group:")
    for age_group in count_students_by_age_group(student_db):
        print(age_group)

    insert_multiple_students(student_db, [('David', 21), ('Eva', 20)])
    print("\nAfter inserting multiple students:")
    print_rows(student_db)
    
    print("\nPaginated results (page 1, limit 2):")
    for student in get_paginated_students(student_db, 1, 2):
        print(student)
    
    course_db = 'courses.db'
    create_students_database(course_db)
    create_courses_table()
    insert_students('Math', 1)  # Assuming Alice has id=1
    insert_students('Science', 1)  # Assuming Alice has id=1
    insert_students('History', 2)  # Assuming Charlie has id=2
    
    print("\nStudents with their courses:")
    for row in fetch_students_with_courses('students.db'):
        print(row)
    
    create_index_on_age('students.db')
    
    export_students_to_csv('students.db', 'students.csv')
    
    if check_table_exists('students.db', 'students'):
        print("\nTable 'students' exists.")