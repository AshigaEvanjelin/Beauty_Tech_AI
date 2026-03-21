from flask import Blueprint, request, jsonify
import os
import cv2
import numpy as np
import uuid
from werkzeug.utils import secure_filename
from models import db, SkinHairAnalysis, Recommendation, HomeCare
from routes.auth import token_required
from config import Config
from datetime import datetime
import random

analysis_bp = Blueprint('analysis', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_mock_analysis(filepath):
    # This is a mock function simulating OpenCV processing
    # In a real scenario, this would load the image using cv2.imread and run ML models
    # img = cv2.imread(filepath)
    # ... CV logic ...
    
    skin_score = round(random.uniform(40.0, 95.0), 1)
    hair_score = round(random.uniform(40.0, 95.0), 1)
    
    acne_levels = ['Low', 'Medium', 'High']
    hair_damage = ['Minimal', 'Moderate', 'Severe']
    
    return {
        'skin_score': skin_score,
        'hair_score': hair_score,
        'acne_level': random.choice(acne_levels) if skin_score < 75 else 'Low',
        'hair_damage_level': random.choice(hair_damage) if hair_score < 75 else 'Minimal'
    }

def generate_recommendations(user_id, analysis_data):
    recs = []
    
    if analysis_data['acne_level'] == 'High':
        recs.append(Recommendation(user_id=user_id, recommended_service='Acne Clearing Facial', priority='High'))
    elif analysis_data['acne_level'] == 'Medium':
        recs.append(Recommendation(user_id=user_id, recommended_service='Deep Cleansing Facial', priority='Medium'))
    else:
        recs.append(Recommendation(user_id=user_id, recommended_service='Hydrating Glow Mask', priority='Low'))
        
    if analysis_data['hair_damage_level'] == 'Severe':
        recs.append(Recommendation(user_id=user_id, recommended_service='Keratin Treatment', priority='High'))
    elif analysis_data['hair_damage_level'] == 'Moderate':
        recs.append(Recommendation(user_id=user_id, recommended_service='Deep Conditioning Hair Spa', priority='Medium'))
    else:
        recs.append(Recommendation(user_id=user_id, recommended_service='Regular Trimming & Wash', priority='Low'))
        
    db.session.add_all(recs)
    
    # Generate Home Care
    home_care = HomeCare.query.filter_by(user_id=user_id).first()
    if not home_care:
        home_care = HomeCare(user_id=user_id)
        db.session.add(home_care)
        
    if analysis_data['acne_level'] in ['High', 'Medium']:
        home_care.morning_routine = 'Salicylic Acid Cleanser, Niacinamide Serum, Oil-free Sunscreen'
        home_care.night_routine = 'Gentle Cleanser, Retinol (2x a week), Lightweight Moisturizer'
    else:
        home_care.morning_routine = 'Hydrating Cleanser, Vitamin C Serum, Sunscreen'
        home_care.night_routine = 'Double Cleanse, Hyaluronic Acid, Rich Night Cream'
        
    if analysis_data['hair_damage_level'] in ['Severe', 'Moderate']:
        home_care.hair_care = 'Sulfate-free Shampoo, Repairing Hair Mask (weekly), Argan Oil Serum'
    else:
        home_care.hair_care = 'Gentle Daily Shampoo, Lightweight Conditioner, Heat Protectant before styling'
        
    return recs, home_care

@analysis_bp.route('/upload', methods=['POST'])
@token_required
def upload_and_analyze(current_user):
    if 'file' not in request.files:
        return jsonify({'message': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'message': 'No selected file'}), 400
        
    if file and allowed_file(file.filename):
        if not os.path.exists(Config.UPLOAD_FOLDER):
            os.makedirs(Config.UPLOAD_FOLDER)
            
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}_{filename}"
        filepath = os.path.join(Config.UPLOAD_FOLDER, unique_filename)
        file.save(filepath)
        
        # Run Mock Analysis
        analysis_results = generate_mock_analysis(filepath)
        
        # Save Analysis to DB
        new_analysis = SkinHairAnalysis(
            user_id=current_user.user_id,
            skin_score=analysis_results['skin_score'],
            hair_score=analysis_results['hair_score'],
            acne_level=analysis_results['acne_level'],
            hair_damage_level=analysis_results['hair_damage_level'],
            image_path=unique_filename
        )
        db.session.add(new_analysis)
        
        # Generate Recommendations and Home Care
        generate_recommendations(current_user.user_id, analysis_results)
        
        db.session.commit()
        
        return jsonify({
            'message': 'Analysis completed',
            'analysis': {
                'id': new_analysis.analysis_id,
                'skin_score': new_analysis.skin_score,
                'hair_score': new_analysis.hair_score,
                'acne_level': new_analysis.acne_level,
                'hair_damage_level': new_analysis.hair_damage_level,
                'date': new_analysis.date.isoformat()
            }
        }), 200

    return jsonify({'message': 'Invalid file type'}), 400

    return jsonify({'message': 'Invalid file type'}), 400

@analysis_bp.route('/history', methods=['GET'])
@token_required
def get_analysis_history(current_user):
    analyses = SkinHairAnalysis.query.filter_by(user_id=current_user.user_id).order_by(SkinHairAnalysis.date.desc()).all()
    return jsonify([{
        'id': a.analysis_id,
        'skin_score': a.skin_score,
        'hair_score': a.hair_score,
        'acne_level': a.acne_level,
        'hair_damage_level': a.hair_damage_level,
        'date': a.date.isoformat(),
        'image_url': f'/uploads/{a.image_path}'
    } for a in analyses]), 200
  
