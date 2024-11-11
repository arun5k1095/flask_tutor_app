from flask import Flask, render_template, request, redirect, url_for, flash
from models import db, Student, ClassSession
from config import Config
from datetime import datetime
from sqlalchemy.sql import func
import pandas as pd
import matplotlib.pyplot as plt
import os

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

# Manually create the database when the app starts
with app.app_context():
    db.create_all()
    print("Database created successfully!")

@app.route('/')
def dashboard():
    students = Student.query.all()
    total_classes = db.session.query(func.sum(ClassSession.duration)).scalar() or 0
    total_earnings = db.session.query(func.sum(ClassSession.earnings)).scalar() or 0
    return render_template('dashboard.html', students=students, total_classes=total_classes, total_earnings=total_earnings)

@app.route('/add_student', methods=['GET', 'POST'])
def add_student():
    if request.method == 'POST':
        full_name = request.form['full_name']
        email = request.form['email']
        phone = request.form['phone']
        rate_per_hour = float(request.form['rate_per_hour'])
        currency = request.form['currency']
        currency_to_inr = float(request.form['currency_to_inr'])
        new_student = Student(full_name=full_name, email=email, phone=phone,
                              rate_per_hour=rate_per_hour, currency=currency,
                              currency_to_inr=currency_to_inr)
        db.session.add(new_student)
        db.session.commit()
        flash('Student added successfully!')
        return redirect(url_for('dashboard'))
    return render_template('add_student.html')

@app.route('/manage_students')
def manage_students():
    students = Student.query.all()  # Fetch all students from the database
    return render_template('manage_students.html', students=students)

@app.route('/add_class', methods=['GET', 'POST'])
def add_class():
    students = Student.query.all()  # Fetch all students for the dropdown
    if request.method == 'POST':
        student_id = request.form['student_id']
        class_date = request.form['class_date']
        class_time = request.form['class_time']
        duration = float(request.form['duration'])
        student = Student.query.get(student_id)  # Fetch the student by ID
        earnings = duration * student.rate_per_hour

        # Create a new ClassSession
        new_class = ClassSession(
            student_id=student_id,
            date=class_date,
            time=class_time,
            duration=duration,
            earnings=earnings
        )
        db.session.add(new_class)
        db.session.commit()
        flash('Class added successfully!')
        return redirect(url_for('dashboard'))

    return render_template('add_class.html', students=students)


@app.route('/analytics')
def analytics():
    # Query all class sessions and join with student details
    classes = db.session.query(ClassSession, Student).join(Student).all()

    # Prepare data for analysis
    data = []
    for class_session, student in classes:
        data.append({
            'student_name': student.full_name,
            'hours_taught': class_session.duration,
            'earnings': class_session.earnings
        })

    # Convert data to DataFrame
    df = pd.DataFrame(data)

    # Group by student and calculate totals
    if not df.empty:
        summary = df.groupby('student_name').sum().reset_index()
    else:
        summary = pd.DataFrame(columns=['student_name', 'hours_taught', 'earnings'])

    # Generate graphs
    if not summary.empty:
        # Earnings per student
        plt.figure(figsize=(10, 6))
        plt.bar(summary['student_name'], summary['earnings'], color='skyblue')
        plt.title('Earnings per Student')
        plt.xlabel('Student')
        plt.ylabel('Earnings (Currency)')
        plt.xticks(rotation=45)
        earnings_graph_path = os.path.join('static', 'earnings_graph.png')
        plt.savefig(earnings_graph_path)
        plt.close()

        # Hours taught per student
        plt.figure(figsize=(10, 6))
        plt.bar(summary['student_name'], summary['hours_taught'], color='salmon')
        plt.title('Hours Taught per Student')
        plt.xlabel('Student')
        plt.ylabel('Hours')
        plt.xticks(rotation=45)
        hours_graph_path = os.path.join('static', 'hours_graph.png')
        plt.savefig(hours_graph_path)
        plt.close()
    else:
        earnings_graph_path = None
        hours_graph_path = None

    return render_template(
        'analytics.html',
        summary=summary.to_dict(orient='records'),
        earnings_graph=earnings_graph_path,
        hours_graph=hours_graph_path
    )

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))  # Use PORT from environment, default to 5000
    app.run(host='0.0.0.0', port=port, debug=False)