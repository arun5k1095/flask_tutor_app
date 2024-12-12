Version = 2

from flask import Flask, render_template, request, redirect, url_for, flash
from flask_paginate import Pagination, get_page_parameter
from sqlalchemy.sql import func
from models import db, Doctor, Patient, Session
from config import Config
from datetime import datetime
import os
from sqlalchemy_continuum import versioning_manager

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

# Initialize the database
with app.app_context():
    db.create_all()


@app.route('/')
def dashboard():
    total_patients = Patient.query.count()
    total_sessions = Session.query.count()
    total_earnings = db.session.query(func.sum(Session.fee)).scalar() or 0
    return render_template('dashboard.html', total_patients=total_patients, total_sessions=total_sessions,
                           total_earnings=total_earnings)


@app.route('/add_doctor', methods=['GET', 'POST'])
def add_doctor():
    if request.method == 'POST':
        full_name = request.form['full_name']
        email = request.form['email']
        phone = request.form['phone']
        new_doctor = Doctor(full_name=full_name, email=email, phone=phone)
        db.session.add(new_doctor)
        db.session.commit()
        flash('Doctor added successfully!')
        return redirect(url_for('dashboard'))
    return render_template('add_doctor.html')


@app.route('/add_patient', methods=['GET', 'POST'])
def add_patient():
    doctors = Doctor.query.all()
    if request.method == 'POST':
        full_name = request.form['full_name']
        email = request.form['email']
        phone = request.form['phone']
        assigned_doctor_id = request.form['assigned_doctor']
        new_patient = Patient(full_name=full_name, email=email, phone=phone, assigned_doctor_id=assigned_doctor_id)
        db.session.add(new_patient)
        db.session.commit()
        flash('Patient added successfully!')
        return redirect(url_for('dashboard'))
    return render_template('add_patient.html', doctors=doctors)


@app.route('/add_session', methods=['GET', 'POST'])
def add_session():
    patients = Patient.query.all()
    doctors = Doctor.query.all()
    if request.method == 'POST':
        patient_id = request.form['patient_id']
        doctor_id = request.form['doctor_id']
        session_date = request.form['session_date']
        session_time = request.form['session_time']
        duration = float(request.form['duration'])
        fee = float(request.form['fee'])
        new_session = Session(patient_id=patient_id, doctor_id=doctor_id, session_date=session_date,
                              session_time=session_time, duration=duration, fee=fee)
        db.session.add(new_session)
        db.session.commit()
        flash('Session added successfully!')
        return redirect(url_for('dashboard'))
    return render_template('add_session.html', patients=patients, doctors=doctors)


@app.route('/patients')
def manage_patients():
    # Fetch the current page number from query parameters
    page = request.args.get("page", default=1, type=int)
    per_page = 3  # Number of records per page

    # Use the updated paginate method
    patients_pagination = Patient.query.paginate(page=page, per_page=per_page)

    return render_template(
        'manage_patients.html',
        patients=patients_pagination.items,
        pagination=patients_pagination
    )



@app.route('/analytics')
def analytics():
    # Explicitly define the join conditions to avoid ambiguity
    sessions = db.session.query(
        Session.id.label('session_id'),
        Patient.full_name.label('patient_name'),
        Doctor.full_name.label('doctor_name'),
        Session.session_date,
        Session.session_time,
        Session.duration,
        Session.fee
    ).join(Patient, Session.patient_id == Patient.id) \
     .join(Doctor, Session.doctor_id == Doctor.id) \
     .all()

    # Prepare data for the template
    data = []
    for session in sessions:
        data.append({
            'session_id': session.session_id,
            'patient_name': session.patient_name,
            'doctor_name': session.doctor_name,
            'session_date': session.session_date.strftime('%Y-%m-%d'),
            'session_time': session.session_time.strftime('%H:%M'),
            'duration': session.duration,
            'fee': session.fee,
        })

    return render_template('analytics.html', data=data)





# Main entry point
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
