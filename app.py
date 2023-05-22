from reportlab.lib.units import inch
from flask import send_file
from flask import send_file, make_response, Flask, render_template, request, redirect, url_for, send_from_directory
from flask_sqlalchemy import SQLAlchemy
import sqlite3
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO
import os
import logging


# code for the connectivity
app = Flask(__name__, static_folder='static', template_folder='templates')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///fml.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# homepage


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
        cursor.execute(
            "SELECT passwd FROM login WHERE id in (select id from login where id like 'hod%') and id=?", (id,))
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
                return render_template('faculty.html', id=id)
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

            # Insert new faculty member into database
            conn = sqlite3.connect('fms.sqlite3')
            cursor = conn.cursor()
            str = 'INSERT INTO Faculty (id, name, qualification, dob, contactno) VALUES (?, ?, ?, ?, ?)'
            val = [faculty_id, faculty_name, faculty_qualification,
                   faculty_dob, faculty_contact_number]
            cursor.execute(str, val)
            cursor.execute('INSERT INTO LOGIN VALUES(?,?)',
                           [faculty_id, faculty_id])
            conn.commit()
            conn.close()

            # Redirect to faculty page
            return render_template('hod.html')

        except Exception as e:
            print(e)
            return "Error: " + str(e)

    # Render the add faculty form
    return render_template('addfaculty.html', displayid='yes')


@app.route('/hod/all')
def all_faculty():
    conn = sqlite3.connect('fms.sqlite3')
    cur = conn.cursor()
    cur.execute("SELECT * FROM Faculty")
    rows = cur.fetchall()
    conn.close()
    if rows:
        return render_template('displayfac.html', rows=rows)
    else:
        return render_template('displayfac.html', error='No faculties found')


@app.route('/hod/<string:id>')
def faculty(id):
    conn = sqlite3.connect('fms.sqlite3')
    cur = conn.cursor()
    cur.execute('SELECT * FROM faculty WHERE id=?', (id,))
    row = cur.fetchone()
    conn.close()
    if row:
        return render_template('displayfac.html', rows=[row])
    else:
        return "No such faculty"


@app.route('/upload/<string:id>', methods=['GET', 'POST'])
def upload_file(id):
    if request.method == 'POST':
        # Get the form data
        title = request.form['title']
        year = request.form['year']
        journal = request.form['journal']
        pdf_file = request.files['pdf_file'].read()

        # Save the PDF file to the SQLite database
        conn = sqlite3.connect('fms.sqlite3')
        cur = conn.cursor()
        cur.execute('INSERT INTO pdfs(id, title, year, pdf_file,journel) VALUES (?, ?, ?, ?, ?)',
                    (id, title, year, pdf_file, journal))
        conn.commit()
        conn.close()

        return render_template('faculty.html', id=id)

    return render_template('upload.html', id=id)


@app.route('/fac/<string:id>/uploadcer', methods=['GET', 'POST'])
def upload_file_certificate(id):
    if request.method == 'POST':
        # Get the form data
        title = request.form['title']
        pdf_file = request.files['certificate_file'].read()
        # Save the PDF file to the SQLite database
        conn = sqlite3.connect('fms.sqlite3')
        cur = conn.cursor()
        cur.execute('INSERT INTO certificate(id, title, pdf_file) VALUES (?, ?, ?)',
                    (id, title, pdf_file))
        conn.commit()
        conn.close()

        return render_template('faculty.html', id=id)

    return render_template('certificate.html', id=id)


@app.route('/display')
def display_files():
    # Retrieve all PDF files from the database
    conn = sqlite3.connect('fms.sqlite3')
    cur = conn.cursor()
    cur.execute('SELECT pdf_file FROM pdfs')
    pdf_files = cur.fetchall()
    conn.close()
    return render_template('display.html', pdf_files=pdf_files)


@app.route('/<string:id>/delete')
def delete(id):
    conn = sqlite3.connect('fms.sqlite3')
    cur = conn.cursor()
    cur.execute('DELETE FROM Faculty WHERE id=?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('all_faculty'))


@app.route('/download_pdf/<int:id>')
def download_pdf(id):
    conn = sqlite3.connect('fms.sqlite3')
    cur = conn.cursor()
    cur.execute("SELECT name, data FROM files WHERE id=?", (id,))
    row = cur.fetchone()
    conn.close()
    if row:
        filename = row[0]
        filedata = row[1]
        return send_file(filedata, attachment_filename=filename, as_attachment=True)
    else:
        return "No PDF found"


@app.route('/<string:id>/update', methods=['GET', 'POST'])
def update(id):
    if request.method == 'POST':
        name = request.form['name']
        qualification = request.form['qualification']
        dob = request.form['dob']
        contact = request.form['contact']

        conn = sqlite3.connect('fms.sqlite3')
        cur = conn.cursor()
        str = 'UPDATE Faculty SET name=?, qualification=?, dob=?, contactno=? WHERE id=?'
        val = [name, qualification, dob, contact, id]
        cur.execute(str, val)
        conn.commit()
        conn.close()

        return redirect(url_for('all_faculty'))

    return render_template('update.html')


@app.route('/fac/<string:id>/update', methods=['GET', 'POST'])
def update_fac(id):
    if request.method == 'POST':
        name = request.form['name']
        qualification = request.form['qualification']
        dob = request.form['dob']
        contact = request.form['contact']

        conn = sqlite3.connect('fms.sqlite3')
        cur = conn.cursor()
        str = 'UPDATE Faculty SET name=?, qualification=?, dob=?, contactno=? WHERE id=?'
        val = [name, qualification, dob, contact, id]
        cur.execute(str, val)
        conn.commit()
        conn.close()

        return render_template('faculty.html')

    return render_template('update.html')


@app.route('/fac/<string:id>/updatepasswd', methods=['GET', 'POST'])
def update_fac_passwd(id):
    if request.method == 'POST':
        passwd = request.form['passwd']
        conn = sqlite3.connect('fms.sqlite3')
        print("connection")
        cur = conn.cursor()

        cur.execute('UPDATE Login SET passwd=? WHERE id=?', (passwd, id))
        conn.commit()
        conn.close()

        return render_template('faculty.html')

    return render_template('updatepasswd.html')


@app.route('/hod/filter', methods=['GET', 'POST'])
def filter():
    if request.method == 'POST':
        year = request.form['year']
        conn = sqlite3.connect('fms.sqlite3')
        c = conn.cursor()
        c.execute('''SELECT pdfs.title,pdfs.journel, pdfs.year, faculty.name
                     FROM pdfs
                     JOIN faculty ON pdfs.id = faculty.id
                     WHERE pdfs.year = ?''', (year,))
        data = c.fetchall()
        conn.close()
        return render_template('filter.html', data=data, year=year)
    else:
        return render_template('filter.html')


@app.route('/portfolio/<string:faculty_id>')
def portfolio(faculty_id):
    conn = sqlite3.connect('fms.sqlite3')
    cur = conn.cursor()

    # Fetch faculty information from database
    cur.execute(
        "SELECT id, name, qualification, dob, contactno FROM faculty WHERE id=?", (faculty_id,))
    faculty_info = cur.fetchone()

    # Fetch publications of faculty member from database
    cur.execute(
        "SELECT title, year, journel FROM pdfs WHERE id=?", (faculty_id,))
    publications = cur.fetchall()

    # Close database connection
    conn.close()

    # Render template for portfolio page
    return render_template('portfolio.html', id=faculty_id, faculty_info=faculty_info, publications=publications)


@app.route('/download/<string:publication_id>')
def download_file(publication_id):
    conn = sqlite3.connect('fms.sqlite3')
    cur = conn.cursor()

    # Fetch file from database using publication ID
    cur.execute(
        "SELECT title, pdf_file FROM pdfs WHERE id=?", (publication_id,))
    publication = cur.fetchone()

    # Close database connection
    conn.close()

    # Set response headers for file download
    headers = {
        "Content-Disposition": "attachment; filename=" + publication[0] + ".pdf"
    }

    # Create a file-like object from the bytes data
    file = BytesIO(publication[1])

    # Create a Flask response object with the file contents and headers
    response = make_response(send_file(file, mimetype='application/pdf'))
    response.headers = headers

    # Return the response object
    return response


@app.route('/generate_pdf/<string:faculty_id>')
def generate_pdf(faculty_id):
    # Connect to the database
    conn = sqlite3.connect('fms.sqlite3')
    cur = conn.cursor()

    # Fetch the data for the specified faculty ID
    cur.execute(
        "SELECT id, name, qualification, dob, contactno FROM faculty WHERE id = ?", (faculty_id,))
    faculty_data = cur.fetchone()

    cur.execute("SELECT title, year FROM pdfs WHERE id =?", (faculty_id,))
    publication_data = cur.fetchall()

    cur.execute("SELECT title FROM certificate WHERE id =?", (faculty_id,))
    certificate_data = cur.fetchall()

    # Process the data
    summary_data = {
        'id': faculty_data[0],
        'name': faculty_data[1],
        'qualifications': faculty_data[2],
        'dob': faculty_data[3],
        'contact_number': faculty_data[4],
        'publications': [],
        'certifications': []
    }
    for publication in publication_data:
        summary_data['publications'].append({
            'title': publication[0],
            'year_of_publication': publication[1],
        })

    for certificates in certificate_data:
        summary_data['certifications'].append({
            'title': certificates[0],
        })

    # Generate the PDF
    pdf_buffer = BytesIO()
    pdf = canvas.Canvas(pdf_buffer, pagesize=letter)
    pdf.setTitle(f"{faculty_data[1]} Resume")

    # Set font and size
    pdf.setFont('Helvetica-Bold', 24)

    # Add title
    pdf.drawCentredString(
        letter[0] / 2, letter[1] - inch, f"{faculty_data[1]} Portfolio")

    # Set font and size for rest of text
    pdf.setFont('Helvetica', 12)

    # Add personal information
    pdf.drawString(100, 650, f"ID: {faculty_data[0]}")
    pdf.drawString(100, 625, f"Qualifications: {faculty_data[2]}")
    pdf.drawString(100, 600, f"DOB: {faculty_data[3]}")
    pdf.drawString(100, 575, f"Contact Number: {faculty_data[4]}")

    # Add publications
    pdf.setFont('Helvetica-Bold', 16)
    publications_text = "Publications:"
    publications_text_width = pdf.stringWidth(
        publications_text, 'Helvetica-Bold', 16)
    pdf.drawCentredString(letter[0] / 2, 500, publications_text)
    pdf.line(100, 490, letter[0] - 100, 490)

    # Set font and size for table
    pdf.setFont('Helvetica-Bold', 12)

    # Define table headers
    pdf.drawString(120, 470, "Title")
    pdf.drawString(350, 470, "Year of Publication")

    # Set font and size for table data
    pdf.setFont('Helvetica', 12)

    y = 450
    for publication in summary_data['publications']:
        pdf.drawString(120, y, publication['title'])
        pdf.drawString(350, y, str(publication['year_of_publication']))
        y -= 20

    # Add certifications
    pdf.setFont('Helvetica-Bold', 16)
    certification_text = "Certifications :"
    certification_text_width = pdf.stringWidth(
        certification_text, 'Helvetica-Bold', 16)
    pdf.drawCentredString(letter[0] / 2, y-40, certification_text)
    pdf.line(100, y-50, letter[0] - 100, y-50)
    y -= 50

    pdf.setFont('Helvetica-Bold', 12)

    # Define table headers
    certification_text = "Title"
    certification_text_width = pdf.stringWidth(
        certification_text, 'Helvetica-Bold', 12)
    pdf.drawCentredString(letter[0] / 2, y-20, certification_text)

    # Set font and size for table data
    pdf.setFont('Helvetica', 12)

    y = y-45
    for publication in summary_data['certifications']:
        pdf.drawCentredString(letter[0] / 2, y, publication['title'])
        y -= 20

    # Save the PDF
    pdf.save()

    # Return the PDF file to the user for download
    pdf_buffer.seek(0)
    return send_file(pdf_buffer, as_attachment=True, download_name=f'{faculty_data[1]}_portfolio.pdf', mimetype='application/pdf')


if __name__ == "__ main__":
    app.run()

