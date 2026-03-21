from flask import Blueprint, request, jsonify
from models import db, Appointment, ServiceHistory
from routes.auth import token_required
from datetime import datetime

appointments_bp = Blueprint('appointments', __name__)

@appointments_bp.route('/', methods=['POST'])
@token_required
def book_appointment(current_user):
    data = request.get_json()
    
    try:
        appt_date = datetime.fromisoformat(data['date'].replace('Z', '+00:00'))
    except ValueError:
        return jsonify({'message': 'Invalid date format. Use ISO format.'}), 400

    new_appt = Appointment(
        user_id=current_user.user_id,
        service=data['service'],
        date=appt_date,
        status='pending'
    )
    db.session.add(new_appt)
    db.session.commit()
    return jsonify({'message': 'Appointment booked successfully!'}), 201

@appointments_bp.route('/', methods=['GET'])
@token_required
def get_appointments(current_user):
    if current_user.role == 'customer':
        appts = Appointment.query.filter_by(user_id=current_user.user_id).order_by(Appointment.date).all()
    else:
        # Staff or Owner can see all upcoming
        appts = Appointment.query.order_by(Appointment.date).all()
        
    return jsonify([{
        'id': a.appointment_id,
        'user_id': a.user_id,
        'service': a.service,
        'date': a.date.isoformat() + 'Z' if not a.date.tzinfo else a.date.isoformat(),
        'status': a.status
    } for a in appts]), 200

@appointments_bp.route('/<int:id>/status', methods=['PUT'])
@token_required
def update_status(current_user, id):
    if current_user.role == 'customer':
        return jsonify({'message': 'Unauthorized'}), 403
        
    data = request.get_json()
    appt = Appointment.query.get(id)
    if not appt:
        return jsonify({'message': 'Appointment not found'}), 404
        
    appt.status = data.get('status', appt.status)
    
    # If completed, add to service history
    if appt.status == 'completed':
        history = ServiceHistory(
            user_id=appt.user_id,
            treatment=appt.service,
            date=datetime.utcnow(),
            results=data.get('results', 'Treatment completed successfully')
        )
        db.session.add(history)
        
    db.session.commit()
    return jsonify({'message': f'Status updated to {appt.status}'}), 200
