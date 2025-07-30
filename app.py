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

# Database Models
class Song(db.Model):
    __tablename__ = 'songs'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    artist = db.Column(db.String(200), nullable=False)
    lyrics = db.Column(db.Text, nullable=False)
    maqam = db.Column(db.String(50), nullable=False)
    style = db.Column(db.String(50), nullable=False)
    tempo = db.Column(db.Integer, nullable=False)
    emotion = db.Column(db.String(50), nullable=False)
    region = db.Column(db.String(50), nullable=False)
    composer = db.Column(db.String(200))
    poem_bahr = db.Column(db.String(50))
    filename = db.Column(db.String(255))
    file_size = db.Column(db.Integer)
    file_type = db.Column(db.String(10))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'artist': self.artist,
            'lyrics': self.lyrics,
            'maqam': self.maqam,
            'style': self.style,
            'tempo': self.tempo,
            'emotion': self.emotion,
            'region': self.region,
            'composer': self.composer,
            'poem_bahr': self.poem_bahr,
            'filename': self.filename,
            'file_size': self.file_size,
            'file_size_mb': round(self.file_size / (1024*1024), 2) if self.file_size else 0,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class TrainingSession(db.Model):
    __tablename__ = 'training_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(36), unique=True, nullable=False)
    status = db.Column(db.String(20), default='training')
    progress = db.Column(db.Integer, default=0)
    epochs = db.Column(db.Integer, default=25)
    learning_rate = db.Column(db.Float, default=0.001)
    batch_size = db.Column(db.Integer, default=32)
    songs_used = db.Column(db.Integer, default=0)
    final_accuracy = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)

class GeneratedSong(db.Model):
    __tablename__ = 'generated_songs'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    lyrics = db.Column(db.Text, nullable=False)
    maqam = db.Column(db.String(50), nullable=False)
    style = db.Column(db.String(50), nullable=False)
    tempo = db.Column(db.Integer, nullable=False)
    emotion = db.Column(db.String(50), nullable=False)
    region = db.Column(db.String(50), nullable=False)
    composer = db.Column(db.String(200))
    poem_bahr = db.Column(db.String(50))
    duration = db.Column(db.String(20))
    instruments = db.Column(db.String(50))
    creativity = db.Column(db.Integer)
    generation_time = db.Column(db.Float)
    model_version = db.Column(db.String(50))
    training_session_id = db.Column(db.String(36))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'lyrics': self.lyrics,
            'maqam': self.maqam,
            'style': self.style,
            'tempo': self.tempo,
            'emotion': self.emotion,
            'region': self.region,
            'composer': self.composer,
            'poem_bahr': self.poem_bahr,
            'duration': self.duration,
            'instruments': self.instruments,
            'creativity': self.creativity,
            'generation_time': self.generation_time,
            'model_version': self.model_version,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

# Create tables and add sample data
with app.app_context():
    try:
        db.create_all()
        print("✅ Database tables created successfully!")
        
        # Add sample song if database is empty
        if Song.query.count() == 0:
            sample_song = Song(
                title="Sample Arabic Song",
                artist="Test Artist",
                lyrics="هذه أغنية تجريبية\nبكلمات عربية جميلة\nللاختبار والتجربة",
                maqam="hijaz",
                style="classical",
                tempo=120,
                emotion="romantic",
                region="egyptian",
                composer="Test Composer",
                poem_bahr="baseet",
                filename="sample.mp3",
                file_size=5242880,  # 5MB
                file_type="mp3"
            )
            db.session.add(sample_song)
            db.session.commit()
            print("✅ Sample song added!")
            
    except Exception as e:
        print(f"❌ Database setup error: {e}")

# Basic routes
@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/health')
def health_check():
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
