from flask import Blueprint, request, jsonify
from models import db, Recommendation, HomeCare
from routes.auth import token_required

recommendations_bp = Blueprint('recommendations', __name__)

@recommendations_bp.route('/services', methods=['GET'])
@token_required
def get_recommended_services(current_user):
    recs = Recommendation.query.filter_by(user_id=current_user.user_id).all()
    return jsonify([{
        'id': r.rec_id,
        'service': r.recommended_service,
        'priority': r.priority
    } for r in recs]), 200

@recommendations_bp.route('/homecare', methods=['GET'])
@token_required
def get_home_care(current_user):
    plan = HomeCare.query.filter_by(user_id=current_user.user_id).first()
    if not plan:
        return jsonify({'message': 'No home care plan generated yet'}), 404
        
    return jsonify({
        'id': plan.plan_id,
        'morning_routine': plan.morning_routine,
        'night_routine': plan.night_routine,
        'hair_care': plan.hair_care,
        'created_at': plan.created_at.isoformat()
    }), 200
