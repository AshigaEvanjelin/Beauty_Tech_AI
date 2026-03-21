from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    user_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    age = db.Column(db.Integer)
    gender = db.Column(db.String(20))
    role = db.Column(db.String(20), default='customer') # customer, staff, owner
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    passport = db.relationship('BeautyPassport', backref='user', uselist=False)
    analyses = db.relationship('SkinHairAnalysis', backref='user')
    recommendations = db.relationship('Recommendation', backref='user')
    home_care = db.relationship('HomeCare', backref='user', uselist=False)
    appointments = db.relationship('Appointment', backref='user')
    service_history = db.relationship('ServiceHistory', backref='user')
    hairstyle_selections = db.relationship('HairstyleSelections', backref='user')

class BeautyPassport(db.Model):
    __tablename__ = 'beauty_passports'
    passport_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    skin_type = db.Column(db.String(50))
    hair_type = db.Column(db.String(50))
    concerns = db.Column(db.Text)
    beauty_goal = db.Column(db.Text)
    last_analysis = db.Column(db.DateTime)

class SkinHairAnalysis(db.Model):
    __tablename__ = 'skin_hair_analysis'
    analysis_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    skin_score = db.Column(db.Float)
    hair_score = db.Column(db.Float)
    acne_level = db.Column(db.String(50))
    hair_damage_level = db.Column(db.String(50))
    date = db.Column(db.DateTime, default=datetime.utcnow)
    image_path = db.Column(db.String(255))

class Recommendation(db.Model):
    __tablename__ = 'recommendations'
    rec_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    recommended_service = db.Column(db.String(100), nullable=False)
    priority = db.Column(db.String(20)) # High, Medium, Low

class HomeCare(db.Model):
    __tablename__ = 'home_care'
    plan_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    morning_routine = db.Column(db.Text)
    night_routine = db.Column(db.Text)
    hair_care = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Appointment(db.Model):
    __tablename__ = 'appointments'
    appointment_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    service = db.Column(db.String(100), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='pending') # pending, confirmed, completed, cancelled

class ServiceHistory(db.Model):
    __tablename__ = 'service_history'
    service_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    treatment = db.Column(db.String(100), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    results = db.Column(db.Text)

class HairstyleSelections(db.Model):
    __tablename__ = 'hairstyle_selections'
    selection_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    hairstyle_name = db.Column(db.String(100), nullable=False)
    image_preview = db.Column(db.String(255))
    selected_at = db.Column(db.DateTime, default=datetime.utcnow)
