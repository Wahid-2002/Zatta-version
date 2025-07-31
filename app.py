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

# Routes
@app.route('/health')
def health_check():
    return jsonify({'status': 'healthy'})

# UPLOAD ENDPOINT
@app.route('/api/songs/upload', methods=['POST'])
def upload_song():
    try:
        print("=== UPLOAD REQUEST RECEIVED ===")
        print(f"Files in request: {list(request.files.keys())}")
        print(f"Form data: {dict(request.form)}")
        
        # Check audio file
        if 'audio_file' not in request.files:
            print("❌ No audio_file in request")
            return jsonify({'success': False, 'error': 'No audio file provided'}), 400
        
        audio_file = request.files['audio_file']
        print(f"Audio file: {audio_file.filename}")
        
        if audio_file.filename == '':
            print("❌ Empty audio filename")
            return jsonify({'success': False, 'error': 'No audio file selected'}), 400
        
        # Check lyrics file
        if 'lyrics_file' not in request.files:
            print("❌ No lyrics_file in request")
            return jsonify({'success': False, 'error': 'No lyrics file provided'}), 400
        
        lyrics_file = request.files['lyrics_file']
        print(f"Lyrics file: {lyrics_file.filename}")
        
        if lyrics_file.filename == '':
            print("❌ Empty lyrics filename")
            return jsonify({'success': False, 'error': 'No lyrics file selected'}), 400
        
        # Read lyrics
        try:
            lyrics_content = lyrics_file.read().decode('utf-8')
            print(f"✅ Lyrics read successfully, length: {len(lyrics_content)}")
        except Exception as e:
            print(f"❌ Error reading lyrics: {e}")
            return jsonify({'success': False, 'error': 'Could not read lyrics file'}), 400
        
        # Get form data
        title = request.form.get('title', '').strip()
        artist = request.form.get('artist', '').strip()
        maqam = request.form.get('maqam', '').strip()
        style = request.form.get('style', '').strip()
        tempo = request.form.get('tempo', '').strip()
        emotion = request.form.get('emotion', '').strip()
        region = request.form.get('region', '').strip()
        composer = request.form.get('composer', '').strip()
        poem_bahr = request.form.get('poem_bahr', '').strip()
        
        print(f"Form data - Title: '{title}', Artist: '{artist}', Maqam: '{maqam}'")
        
        # Basic validation
        if not title or not artist:
            print("❌ Missing title or artist")
            return jsonify({'success': False, 'error': 'Title and Artist are required'}), 400
        
        # Convert tempo
        try:
            tempo_int = int(tempo) if tempo else 120
        except:
            tempo_int = 120
        
        # Get file info
        audio_data = audio_file.read()
        file_size = len(audio_data)
        filename = secure_filename(audio_file.filename) if audio_file.filename else 'unknown.mp3'
        
        print(f"Creating song object...")
        
        # Create song
        song = Song(
            title=title,
            artist=artist,
            lyrics=lyrics_content,
            maqam=maqam or 'unknown',
            style=style or 'modern',
            tempo=tempo_int,
            emotion=emotion or 'neutral',
            region=region or 'mixed',
            composer=composer,
            poem_bahr=poem_bahr,
            filename=filename,
            file_size=file_size,
            file_type=filename.split('.')[-1] if '.' in filename else 'mp3',
            created_at=datetime.utcnow()
        )
        
        print(f"Saving to database...")
        
        # Save to database
        db.session.add(song)
        db.session.commit()
        
        print(f"✅ Song saved successfully with ID: {song.id}")
        
        # Verify it was saved
        saved_song = Song.query.get(song.id)
        if saved_song:
            print(f"✅ Verification: Song exists in database")
        else:
            print(f"❌ Verification: Song NOT found in database")
        
        return jsonify({
            'success': True,
            'message': f'Song "{title}" uploaded successfully!',
            'song_id': song.id,
            'file_size': f'{file_size / (1024*1024):.2f} MB'
        })
        
    except Exception as e:
        print(f"❌ Upload error: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': f'Upload failed: {str(e)}'}), 500

# LIST SONGS ENDPOINT
@app.route('/api/songs/list')
def list_songs():
    try:
        print("=== LIST SONGS REQUEST ===")
        songs = Song.query.order_by(Song.created_at.desc()).all()
        print(f"Found {len(songs)} songs in database")
        
        songs_data = []
        for song in songs:
            song_dict = song.to_dict()
            songs_data.append(song_dict)
            print(f"Song: {song_dict['title']} by {song_dict['artist']}")
        
        return jsonify({
            'success': True,
            'songs': songs_data
        })
        
    except Exception as e:
        print(f"❌ List songs error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# UPDATE SONG ENDPOINT
@app.route('/api/songs/<int:song_id>', methods=['PUT'])
def update_song(song_id):
    try:
        song = Song.query.get_or_404(song_id)
        data = request.get_json()
        
        # Update fields
        song.title = data.get('title', song.title)
        song.artist = data.get('artist', song.artist)
        song.lyrics = data.get('lyrics', song.lyrics)
        song.maqam = data.get('maqam', song.maqam)
        song.style = data.get('style', song.style)
        song.tempo = int(data.get('tempo', song.tempo))
        song.emotion = data.get('emotion', song.emotion)
        song.region = data.get('region', song.region)
        song.composer = data.get('composer', song.composer)
        song.poem_bahr = data.get('poem_bahr', song.poem_bahr)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Song "{song.title}" updated successfully!',
            'song_id': song.id
        })
        
    except Exception as e:
        print(f"❌ Update song error: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

# DELETE SONG ENDPOINT
@app.route('/api/songs/<int:song_id>', methods=['DELETE'])
def delete_song(song_id):
    try:
        song = Song.query.get_or_404(song_id)
        db.session.delete(song)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Song deleted successfully!'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

# DASHBOARD STATS ENDPOINT
@app.route('/api/dashboard/stats')
def dashboard_stats():
    try:
        songs_count = Song.query.count()
        total_size = db.session.query(db.func.sum(Song.file_size)).scalar() or 0
        
        maqams = db.session.query(Song.maqam).distinct().all()
        regions = db.session.query(Song.region).distinct().all()
        
        latest_training = TrainingSession.query.order_by(TrainingSession.created_at.desc()).first()
        is_training = latest_training and latest_training.status == 'training' if latest_training else False
        model_accuracy = latest_training.final_accuracy if latest_training and latest_training.final_accuracy else 0
        
        return jsonify({
            'success': True,
            'stats': {
                'songs_count': songs_count,
                'total_songs': songs_count,
                'total_size': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2) if total_size else 0,
                'maqams': [m[0] for m in maqams],
                'regions': [r[0] for r in regions],
                'training_sessions': TrainingSession.query.count(),
                'generated_songs': GeneratedSong.query.count(),
                'generated_count': GeneratedSong.query.count(),
                'is_training': is_training,
                'model_accuracy': model_accuracy
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# TRAINING ENDPOINTS
@app.route('/api/training/status')
def training_status():
    try:
        latest_session = TrainingSession.query.order_by(TrainingSession.created_at.desc()).first()
        
        if not latest_session:
            return jsonify({
                'success': True,
                'status': {
                    'is_training': False, 'progress': 0, 'current_epoch': 0,
                    'current_loss': 0, 'status': 'not_started'
                }
            })
        
        if latest_session.status == 'training' and latest_session.progress < 100:
            latest_session.progress = min(100, latest_session.progress + random.randint(2, 8))
            if latest_session.progress >= 100:
                latest_session.status = 'completed'
                latest_session.final_accuracy = random.uniform(0.85, 0.95)
                latest_session.completed_at = datetime.utcnow()
            db.session.commit()
        
        return jsonify({
            'success': True,
            'status': {
                'is_training': latest_session.status == 'training',
                'progress': latest_session.progress,
                'current_epoch': int(latest_session.progress * latest_session.epochs / 100),
                'current_loss': round(random.uniform(0.1, 0.5), 3),
                'status': latest_session.status,
                'session_id': latest_session.session_id
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/training/start', methods=['POST'])
def start_training():
    try:
        songs_count = Song.query.count()
        if songs_count < 1:
            return jsonify({
                'success': False, 
                'error': f'Need at least 1 song to start training. Currently have {songs_count} songs.'
            }), 400
        
        data = request.get_json() or {}
        session_id = str(uuid.uuid4())
        
        training_session = TrainingSession(
            session_id=session_id, status='training', progress=0,
            epochs=int(data.get('epochs', 25)),
            learning_rate=float(data.get('learning_rate', 0.001)),
            batch_size=int(data.get('batch_size', 32)),
            songs_used=songs_count
        )
        
        db.session.add(training_session)
        db.session.commit()
        
        return jsonify({
            'success': True, 'session_id': session_id,
            'message': 'Training started successfully!',
            'estimated_time': '30-45 minutes'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/training/stop', methods=['POST'])
def stop_training():
    try:
        latest_session = TrainingSession.query.filter_by(status='training').order_by(TrainingSession.created_at.desc()).first()
        
        if latest_session:
            latest_session.status = 'stopped'
            latest_session.completed_at = datetime.utcnow()
            db.session.commit()
            return jsonify({'success': True, 'message': 'Training stopped successfully!'})
        else:
            return jsonify({'success': False, 'error': 'No active training session found'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

# GENERATION ENDPOINTS
@app.route('/api/generation/generate', methods=['POST'])
def generate_music():
    try:
        # Handle both file upload and JSON data
        lyrics_content = None
        
        if 'lyrics_file' in request.files:
            lyrics_file = request.files['lyrics_file']
            if lyrics_file.filename and lyrics_file.filename.endswith('.txt'):
                lyrics_content = lyrics_file.read().decode('utf-8')
        
        if not lyrics_content:
            data = request.get_json()
            if data and data.get('lyrics'):
                lyrics_content = data['lyrics']
            else:
                return jsonify({'success': False, 'error': 'No lyrics provided'}), 400
        
        # Get parameters
        if request.content_type and request.content_type.startswith('multipart/form-data'):
            maqam = request.form.get('maqam', 'hijaz')
            style = request.form.get('style', 'modern')
            tempo = int(request.form.get('tempo', 120))
            emotion = request.form.get('emotion', 'neutral')
            region = request.form.get('region', 'mixed')
            title = request.form.get('title', f'Generated Song {GeneratedSong.query.count() + 1}')
        else:
            data = request.get_json() or {}
            maqam = data.get('maqam', 'hijaz')
            style = data.get('style', 'modern')
            tempo = int(data.get('tempo', 120))
            emotion = data.get('emotion', 'neutral')
            region = data.get('region', 'mixed')
            title = data.get('title', f'Generated Song {GeneratedSong.query.count() + 1}')
        
        generated_song = GeneratedSong(
            title=title,
            lyrics=lyrics_content,
            maqam=maqam,
            style=style,
            tempo=tempo,
            emotion=emotion,
            region=region,
            duration='Medium',
            instruments='Modern',
            creativity=7,
            generation_time=round(random.uniform(2.0, 5.0), 1),
            model_version='v1.0',
            training_session_id='demo'
        )
        
        db.session.add(generated_song)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Song "{generated_song.title}" generated successfully!',
            'song_id': generated_song.id,
            'generation_time': f'{generated_song.generation_time} seconds'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/generation/list')
def list_generated_songs():
    try:
        songs = GeneratedSong.query.order_by(GeneratedSong.created_at.desc()).all()
        return jsonify({'success': True, 'songs': [song.to_dict() for song in songs]})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/generation/<int:song_id>', methods=['DELETE'])
def delete_generated_song(song_id):
    try:
        song = GeneratedSong.query.get_or_404(song_id)
        db.session.delete(song)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Generated song deleted successfully!'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

# Catch-all route for frontend routing
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
