from flask import Blueprint, request, jsonify
import os
import cv2
import numpy as np
import uuid
from werkzeug.utils import secure_filename
from models import db, HairstyleSelections, BeautyPassport
from routes.auth import token_required
from config import Config

hairstyle_bp = Blueprint('hairstyle', __name__)

# Load OpenCV's built-in detectors
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')

HAIRSTYLES = [
    {"id": "bob_cut", "name": "Bob Cut", "image": "bob_cut.png"},
    {"id": "curly_style", "name": "Curly Style", "image": "curly_style-removebg-preview.png"},
    {"id": "layer_cut", "name": "Layer Cut", "image": "layer_cut-removebg-preview.png"},
    {"id": "long_waves", "name": "Long Waves", "image": "long_waves-removebg-preview.png"}
]

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg'}

def overlay_transparent(background, overlay, x, y):
    """
    Overlays a transparent PNG onto a background image.
    x, y are the top-left coordinates of the overlay.
    """
    background_width = background.shape[1]
    background_height = background.shape[0]

    if x >= background_width or y >= background_height:
        return background

    h, w = overlay.shape[0], overlay.shape[1]

    # Handle coordinates going off-screen (negative)
    if x < 0:
        overlay = overlay[:, abs(x):]
        w = overlay.shape[1]
        x = 0
    if y < 0:
        overlay = overlay[abs(y):, :]
        h = overlay.shape[0]
        y = 0

    if x + w > background_width:
        w = background_width - x
        overlay = overlay[:, :w]

    if y + h > background_height:
        h = background_height - y
        overlay = overlay[:h]

    if overlay.shape[2] < 4:
        background[y:y+h, x:x+w] = overlay
        return background

    overlay_image = overlay[..., :3]
    mask = overlay[..., 3:] / 255.0

    background[y:y+h, x:x+w] = (1.0 - mask) * background[y:y+h, x:x+w] + mask * overlay_image

    return background

def apply_hairstyle(base_image_path, hairstyle_id):
    """
    Reads the base image, detects facial bounding box and eyes,
    and overlays the requested hairstyle image with precision alignment.
    """
    style = next((s for s in HAIRSTYLES if s['id'] == hairstyle_id), None)
    if not style:
        return None
    hairstyle_img_name = style['image']
    
    img = cv2.imread(base_image_path)
    if img is None:
        return None

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.3, 5)

    if len(faces) == 0:
        return None

    (fx, fy, fw, fh) = faces[0]
    
    # Detect eyes for even better alignment
    roi_gray = gray[fy:fy+fh, fx:fx+fw]
    eyes = eye_cascade.detectMultiScale(roi_gray)
    
    # Calculate face center
    center_x = fx + fw // 2
    if len(eyes) >= 2:
        # Sort by x coordinate to get left and right
        eyes = sorted(eyes, key=lambda e: e[0])
        left_eye = eyes[0]
        right_eye = eyes[-1]
        # Eye midpoint
        center_x = fx + (left_eye[0] + right_eye[0] + right_eye[2]) // 2
        eye_y = fy + (left_eye[1] + right_eye[1]) // 2
    else:
        eye_y = fy + int(fh * 0.35) # Approx eye level if not found
    
    # Load hairstyle
    possible_paths = [
        os.path.join(os.path.dirname(Config.BASE_DIR), 'assets', 'hairstyles', hairstyle_img_name),
        os.path.join('backend', 'static', 'hairstyles', hairstyle_img_name),
    ]
    hair_path = next((p for p in possible_paths if os.path.exists(p)), None)
    if not hair_path:
        raise FileNotFoundError(f"Hairstyle {hairstyle_id} missing.")
        
    hair_img = cv2.imread(hair_path, cv2.IMREAD_UNCHANGED)
    
    # Precise Scaling:
    # Most hairstyle assets are centered in a square 500x500 box
    # We want the 'face hole' (approx 100-150px in the asset) to match the face width
    scale_factor = (fw * 2.5) / 500.0
    
    # Tweaks for different styles
    if hairstyle_id == "bob_cut":
        scale_factor *= 0.95 
    elif hairstyle_id == "curly_style":
        scale_factor *= 1.1

    hair_w = int(hair_img.shape[1] * scale_factor)
    hair_h = int(hair_img.shape[0] * scale_factor)
    hair_resized = cv2.resize(hair_img, (hair_w, hair_h))
    
    # Alignment:
    # Align horizontal center of hair with face center
    start_x = center_x - (hair_w // 2)
    # Align 'eye level' of hair (approx 40% down) with eyes
    start_y = eye_y - int(hair_h * 0.42)
    
    output_img = img.copy()
    output_img = overlay_transparent(output_img, hair_resized, start_x, start_y)
    
    output_filename = f"preview_{uuid.uuid4()}.jpg"
    output_path = os.path.join(Config.UPLOAD_FOLDER, output_filename)
    cv2.imwrite(output_path, output_img)
    
    return output_filename

@hairstyle_bp.route('/options', methods=['GET'])
@token_required
def get_options(current_user):
    return jsonify(HAIRSTYLES), 200

@hairstyle_bp.route('/upload', methods=['POST'])
@token_required
def upload_photo(current_user):
    if 'file' not in request.files:
        return jsonify({'message': 'No file element'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'message': 'No file selected'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        unique_filename = f"base_{uuid.uuid4()}_{filename}"
        if not os.path.exists(Config.UPLOAD_FOLDER):
            os.makedirs(Config.UPLOAD_FOLDER)
            
        filepath = os.path.join(Config.UPLOAD_FOLDER, unique_filename)
        file.save(filepath)
        
        # Verify face detection exists early on
        img = cv2.imread(filepath)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)
        
        if len(faces) == 0:
            os.remove(filepath)
            return jsonify({'message': 'No face detected in the photo. Please try a clearer selfie.'}), 400
        
        return jsonify({'base_image': unique_filename, 'image_url': f'/uploads/{unique_filename}'}), 200
        
    return jsonify({'message': 'Invalid file'}), 400

@hairstyle_bp.route('/generate', methods=['POST'])
@token_required
def generate_preview(current_user):
    data = request.get_json()
    base_image = data.get('base_image')
    hairstyle_id = data.get('hairstyle_id')
    
    if not base_image or not hairstyle_id:
        return jsonify({'message': 'Missing base_image or hairstyle_id'}), 400
        
    base_path = os.path.join(Config.UPLOAD_FOLDER, base_image)
    if not os.path.exists(base_path):
        return jsonify({'message': 'Base image not found'}), 404
        
    try:
        preview_filename = apply_hairstyle(base_path, hairstyle_id)
        if not preview_filename:
            return jsonify({'message': 'Face detection failed during overlay.'}), 400
            
        return jsonify({
            'preview_image': preview_filename,
            'image_url': f'/uploads/{preview_filename}'
        }), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@hairstyle_bp.route('/select', methods=['POST'])
@token_required
def select_hairstyle(current_user):
    data = request.get_json()
    hairstyle_name = data.get('hairstyle_name')
    image_preview = data.get('preview_image')
    
    if not hairstyle_name or not image_preview:
        return jsonify({'message': 'Missing data'}), 400
        
    selection = HairstyleSelections(
        user_id=current_user.user_id,
        hairstyle_name=hairstyle_name,
        image_preview=image_preview
    )
    db.session.add(selection)
    db.session.commit()
    
    return jsonify({'message': 'Hairstyle saved to your Beauty Passport!'}), 200
