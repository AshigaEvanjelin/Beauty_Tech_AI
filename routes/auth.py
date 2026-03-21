from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import datetime
from models import db, User
from config import Config
from functools import wraps

auth_bp = Blueprint('auth', __name__)

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            token = request.headers['Authorization'].split(" ")[1]
        
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401

        try:
            data = jwt.decode(token, Config.SECRET_KEY, algorithms=["HS256"])
            current_user = User.query.filter_by(user_id=data['user_id']).first()
        except:
            return jsonify({'message': 'Token is invalid!'}), 401

        return f(current_user, *args, **kwargs)
    return decorated

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    hashed_password = generate_password_hash(data['password'], method='pbkdf2:sha256')
    
    # Check if user exists
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'message': 'User already exists!'}), 400

    new_user = User(
        name=data['name'], 
        email=data['email'], 
        password_hash=hashed_password,
        role=data.get('role', 'customer'),
        age=data.get('age'),
        gender=data.get('gender')
    )
    
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({'message': 'Registered successfully!'}), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    
    user = User.query.filter_by(email=data['email']).first()
    
    if not user or not check_password_hash(user.password_hash, data['password']):
        return jsonify({'message': 'Login Unsuccessful. Please check email and password'}), 401

    token = jwt.encode({
        'user_id': user.user_id,
        'role': user.role,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    }, Config.SECRET_KEY, algorithm="HS256")
    
    return jsonify({
        'token': token,
        'user': {
            'id': user.user_id,
            'name': user.name,
            'email': user.email,
            'role': user.role
        }
    }), 200

@auth_bp.route('/me', methods=['GET'])
@token_required
def get_current_user(current_user):
    return jsonify({
        'id': current_user.user_id,
        'name': current_user.name,
        'email': current_user.email,
        'role': current_user.role,
        'age': current_user.age,
        'gender': current_user.gender
    }), 200
