from flask import Blueprint, jsonify, request
from models import db, User, Appointment, ServiceHistory, SkinHairAnalysis, BeautyPassport, Recommendation
from routes.auth import token_required
from sqlalchemy import func

dashboards_bp = Blueprint('dashboards', __name__)

@dashboards_bp.route('/staff/customers', methods=['GET'])
@token_required
def get_customers(current_user):
    if current_user.role not in ['staff', 'owner']:
        return jsonify({'message': 'Unauthorized'}), 403
    
    search_query = request.args.get('search', '')
    print(f"DEBUG: Staff Dashboard customer search with query: '{search_query}'")
    
    if search_query:
        customers = User.query.filter(
            User.role == 'customer', 
            (User.name.ilike(f"%{search_query}%")) | (User.email.ilike(f"%{search_query}%"))
        ).all()
        print(f"DEBUG: Found {len(customers)} matches for '{search_query}'")
    else:
        customers = User.query.filter_by(role='customer').all()
        
    return jsonify([{
        'id': c.user_id,
        'name': c.name,
        'email': c.email,
        'age': c.age,
        'gender': c.gender
    } for c in customers]), 200

@dashboards_bp.route('/user/<int:user_id>', methods=['GET'])
@token_required
def get_user_details(current_user, user_id):
    if current_user.role not in ['staff', 'owner']:
        return jsonify({'message': 'Unauthorized'}), 403
        
    user = User.query.get(user_id)
    if not user:
        return jsonify({'message': 'User not found'}), 404
        
    passport = BeautyPassport.query.filter_by(user_id=user_id).first()
    analysis = SkinHairAnalysis.query.filter_by(user_id=user_id).order_by(SkinHairAnalysis.date.desc()).all()
    recommendations = Recommendation.query.filter_by(user_id=user_id).all()
    
    return jsonify({
        "name": user.name,
        "age": user.age,
        "gender": user.gender,
        "email": user.email,
        "passport": {
            "skin_type": passport.skin_type if passport else "N/A",
            "hair_type": passport.hair_type if passport else "N/A",
            "concerns": passport.concerns if passport else "None",
            "beauty_goal": passport.beauty_goal if passport else "N/A"
        } if passport else None,
        "analysis": [{
            "date": a.date.strftime("%Y-%m-%d"),
            "skin_score": a.skin_score,
            "hair_score": a.hair_score,
            "acne_level": a.acne_level,
            "hair_damage_level": a.hair_damage_level
        } for a in analysis],
        "recommendations": [{
            "service": r.recommended_service,
            "priority": r.priority
        } for r in recommendations]
    }), 200

@dashboards_bp.route('/owner/analytics', methods=['GET'])
@token_required
def get_analytics(current_user):
    if current_user.role != 'owner':
        return jsonify({'message': 'Unauthorized'}), 403
        
    # Popular services
    popular_services = db.session.query(
        ServiceHistory.treatment, 
        func.count(ServiceHistory.service_id).label('count')
    ).group_by(ServiceHistory.treatment).order_by(func.count(ServiceHistory.service_id).desc()).limit(5).all()
    
    # Common skin problems (based on High acne level as a proxy for this mock)
    acne_stats = db.session.query(
        SkinHairAnalysis.acne_level,
        func.count(SkinHairAnalysis.analysis_id)
    ).group_by(SkinHairAnalysis.acne_level).all()
    
    # Total Users
    total_customers = User.query.filter_by(role='customer').count()
    
    # Appointments this month (mocked as total pending/confirmed for now)
    upcoming_appointments = Appointment.query.filter(Appointment.status.in_(['pending', 'confirmed'])).count()
    
    return jsonify({
        'popular_services': [{'service': row[0], 'count': row[1]} for row in popular_services],
        'acne_stats': {row[0]: row[1] for row in acne_stats},
        'total_customers': total_customers,
        'upcoming_appointments': upcoming_appointments,
        'revenue_estimate': upcoming_appointments * 120 # Mock average $120 per service
    }), 200
