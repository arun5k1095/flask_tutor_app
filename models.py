from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    rate_per_hour = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(10), nullable=False)
    currency_to_inr = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f"<Student {self.full_name}>"

class ClassSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    date = db.Column(db.String(20), nullable=False)
    time = db.Column(db.String(10), nullable=False)
    duration = db.Column(db.Float, nullable=False)
    earnings = db.Column(db.Float, nullable=False)

    student = db.relationship('Student', backref='classes')

    def __repr__(self):
        return f"<ClassSession {self.date} {self.time}>"
