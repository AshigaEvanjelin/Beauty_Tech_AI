from flask import Blueprint, request, jsonify
from models import db, BeautyPassport
from routes.auth import token_required
from routes.analysis import allowed_file
import random

passport_bp = Blueprint('passport', __name__)

@passport_bp.route('/', methods=['GET'])
@token_required
def get_passport(current_user):
    passport = BeautyPassport.query.filter_by(user_id=current_user.user_id).first()
    if not passport:
        return jsonify({'message': 'Passport not found, please create one'}), 404
        
    return jsonify({
        'passport_id': passport.passport_id,
        'skin_type': passport.skin_type,
        'hair_type': passport.hair_type,
        'concerns': passport.concerns.split(',') if passport.concerns else [],
        'beauty_goal': passport.beauty_goal,
        'last_analysis': passport.last_analysis
    }), 200

@passport_bp.route('/', methods=['POST', 'PUT'])
@token_required
def update_passport(current_user):
    data = request.get_json()
    passport = BeautyPassport.query.filter_by(user_id=current_user.user_id).first()
    
    is_new = False
    if not passport:
        passport = BeautyPassport(user_id=current_user.user_id)
        db.session.add(passport)
        is_new = True
        
    passport.skin_type = data.get('skin_type', passport.skin_type)
    passport.hair_type = data.get('hair_type', passport.hair_type)
    
    if 'concerns' in data:
        passport.concerns = ','.join(data['concerns']) if isinstance(data['concerns'], list) else data['concerns']
        
    passport.beauty_goal = data.get('beauty_goal', passport.beauty_goal)
    
    db.session.commit()
    
    msg = 'Beauty passport created successfully!' if is_new else 'Beauty passport updated successfully!'
    return jsonify({'message': msg}), 200

@passport_bp.route('/detect', methods=['POST'])
@token_required
def detect_features(current_user):
    if 'file' not in request.files:
        return jsonify({'message': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'message': 'No selected file'}), 400
        
    if file and allowed_file(file.filename):
        skin_types = ['Oily', 'Dry', 'Combination', 'Sensitive', 'Normal']
        hair_types = ['Straight', 'Wavy', 'Curly', 'Coily']
        concerns_list = ['Acne', 'Fine lines', 'Dryness', 'Pigmentation', 'Frizz', 'Thinning hair', 'Dullness']
        
        detected_skin = random.choice(skin_types)
        detected_hair = random.choice(hair_types)
        detected_concerns = random.sample(concerns_list, random.randint(1, 3))
        
        return jsonify({
            'skin_type': detected_skin,
            'hair_type': detected_hair,
            'concerns': ', '.join(detected_concerns)
        }), 200

    return jsonify({'message': 'Invalid file type'}), 400
