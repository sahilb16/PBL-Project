from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import sqlite3
import os
import logging

app = Flask(__name__, static_folder='static', template_folder='templates')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///fml.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/login-hod', methods=['GET', 'POST'])
def loginhod():
    if request.method == 'POST':
        # Check if id and pwd fields are present in the form data
        if 'id' not in request.form or 'pwd' not in request.form:
            return render_template('login-hod.html', error='Missing credentials')

        id = request.form['id']
        password = request.form['pwd']
        conn = sqlite3.connect('fms.sqlite3')
        cursor = conn.cursor()
        cursor.execute('SELECT passwd FROM login WHERE id=?', (id,))
        result = cursor.fetchone()
        if result is None:
            return render_template('login-hod.html', error='User not registered')
        else:
            if password == result[0]:
                return render_template('hod.html')
            else:
                return render_template('login-hod.html', error='Incorrect password')
    return render_template('login-hod.html')


@app.route('/login-fac', methods=['GET', 'POST'])
def loginfac():
    if request.method == 'POST':
        # Check if id and pwd fields are present in the form data
        if 'id' not in request.form or 'pwd' not in request.form:
            return render_template('login-fac.html', error='Missing credentials')

        id = request.form['id']
        password = request.form['pwd']
        conn = sqlite3.connect('fms.sqlite3')
        cursor = conn.cursor()
        cursor.execute('SELECT passwd FROM login WHERE id=?', (id,))
        result = cursor.fetchone()
        if result is None:
            return render_template('login-fac.html', error='User not registered')
        else:
            if password == result[0]:
                return render_template('faculty.html')
            else:
                return render_template('login-fac.html', error='Incorrect password')
    return render_template('login-fac.html')


@app.route('/hod/addfaculty', methods=['GET', 'POST'])
def addfaculty():
    if request.method == 'POST':
        try:
            # Get form data from request
            faculty_id = request.form['id']
            faculty_name = request.form['name']
            faculty_qualification = request.form['qualification']
            faculty_dob = request.form['dob']
            faculty_contact_number = request.form['contact']

            file_certificate = request.files['certificate']
            if not file_certificate:
                return "Error: no file uploaded"

            # Insert new faculty member into database
            conn = sqlite3.connect('fms.sqlite3')
            cursor = conn.cursor()
            cursor.execute('INSERT INTO Faculty (id, name, qualification, certificate, dob, contactno) VALUES (?, ?, ?, ?, ?, ?)', [faculty_id, faculty_name, faculty_qualification, file_certificate.read(),
                                                                                                                                    faculty_dob, faculty_contact_number])
            conn.commit()
            conn.close()

            # Redirect to faculty page
            return render_template('faculty.html')

        except Exception as e:
            print(e)
            return "Error: " + str(e)

    # Render the add faculty form
    return render_template('addfaculty.html')
    #     except Exception as e:
    #         logging.error('Error adding faculty: {}'.format(e))
    #         return 'Error adding faculty: {}'.format(e), 400

    # return render_template('addfaculty.html')


@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files['pdf_file']
        if file:
            # Save the PDF file to a SQLite database
            conn = sqlite3.connect('fms.sqlite3')
            cur = conn.cursor()
            cur.execute('INSERT INTO pdfs (pdf_file) VALUES (?)',
                        (file.read(),))
            conn.commit()
            conn.close()
    return render_template('upload.html')


@app.route('/display')
def display_files():
    # Retrieve all PDF files from the database
    conn = sqlite3.connect('fms.sqlite3')
    cur = conn.cursor()
    cur.execute('SELECT pdf_file FROM pdfs')
    pdf_files = cur.fetchall()
    conn.close()
    return render_template('display.html', pdf_files=pdf_files)


if __name__ == "__ main__":
    app.run()
