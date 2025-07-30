import os
import sys
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from datetime import datetime
import json
import uuid
import time
import random

# Create Flask app
app = Flask(__name__, static_folder='src/static', static_url_path='/')

# Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'asdf#FGSgvasgf$5$WGT')
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size

# Database configuration (using SQLite for now)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///arabic_music_ai.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
CORS(app)
db = SQLAlchemy(app)

# Allowed file extensions
ALLOWED_EXTENSIONS = {'mp3', 'wav', 'flac', 'm4a'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Basic routes
@app.route('/')
def index():
    return "Arabic Music AI is running!"

@app.route('/health')
def health_check():
    return {'status': 'healthy'}

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
