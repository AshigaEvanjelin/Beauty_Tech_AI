from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from models import db
from config import Config
import os

app = Flask(__name__, static_folder='static', static_url_path='/')
app.config.from_object(Config)

CORS(app)
db.init_app(app)

from routes.auth import auth_bp
from routes.passport import passport_bp
from routes.analysis import analysis_bp
from routes.recommendations import recommendations_bp
from routes.appointments import appointments_bp
from routes.dashboards import dashboards_bp
from routes.hairstyle import hairstyle_bp

app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(passport_bp, url_prefix='/api/passport')
app.register_blueprint(analysis_bp, url_prefix='/api/analysis')
app.register_blueprint(recommendations_bp, url_prefix='/api/recommendations')
app.register_blueprint(appointments_bp, url_prefix='/api/appointments')
app.register_blueprint(dashboards_bp, url_prefix='/api/dashboards')
app.register_blueprint(hairstyle_bp, url_prefix='/api/hairstyle')

@app.route('/uploads/<path:filename>')
def serve_uploads(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/hairstyles/<path:filename>')
def serve_hairstyles(filename):
    assets_dir = os.path.join(os.path.dirname(app.root_path), 'assets', 'hairstyles')

    print("App root:", app.root_path)
    print("Assets dir:", assets_dir)
    print("Exists:", os.path.exists(assets_dir))

    return send_from_directory(assets_dir, filename)

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({"status": "BeautyPassport API is running"}), 200

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_react(path):
    if path != "" and os.path.exists(app.static_folder + '/' + path):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print("Database tables created successfully!")
    app.run(debug=True, port=5000)
