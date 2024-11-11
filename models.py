from flask_sqlalchemy import SQLAlchemy
from sqlalchemy_continuum import make_versioned, versioning_manager

db = SQLAlchemy()


# Define the User class
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)



class Doctor(db.Model):
    __versioned__ = {}
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    phone = db.Column(db.String(15), nullable=False)

class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    assigned_doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'), nullable=False)
    assigned_doctor = db.relationship('Doctor', backref=db.backref('patients', lazy=True))

class Session(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'), nullable=False)
    session_date = db.Column(db.Date, nullable=False)
    session_time = db.Column(db.Time, nullable=False)
    duration = db.Column(db.Float, nullable=False)
    fee = db.Column(db.Float, nullable=False)
    patient = db.relationship('Patient', backref=db.backref('sessions', lazy=True))
    doctor = db.relationship('Doctor', backref=db.backref('sessions', lazy=True))
