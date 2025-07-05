from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from celery import Celery
import os
import redis
from dotenv import load_dotenv
import uuid
import json
from datetime import datetime
import logging

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Configure Celery
app.config['CELERY_BROKER_URL'] = os.getenv('REDIS_URL', 'redis://localhost:6379')
app.config['CELERY_RESULT_BACKEND'] = os.getenv('REDIS_URL', 'redis://localhost:6379')

# Initialize Celery
celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)

# Initialize Redis for job tracking
redis_client = redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379'))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Bible stories list
BIBLE_STORIES = [
    "Adam and Eve", "Noah's Ark", "Abraham and Isaac", "Moses and the Exodus",
    "David and Goliath", "Jonah and the Whale", "Daniel in the Lion's Den",
    "Jesus' Birth", "Jesus' Baptism", "The Good Samaritan", "Jesus Feeds 5000",
    "Jesus Walks on Water", "The Resurrection", "Paul's Conversion"
]

@app.route('/')
def index():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'Bible Story Video Generator API',
        'version': '1.0.0'
    })

@app.route('/stories', methods=['GET'])
def get_stories():
    """Get list of available Bible stories"""
    return jsonify({'stories': BIBLE_STORIES})

@app.route('/generate', methods=['POST'])
def generate_video():
    """Start video generation process"""
    try:
        data = request.get_json()
        
        # Validate input
        required_fields = ['story', 'duration', 'resolution', 'tiktok']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Validate story
        if data['story'] not in BIBLE_STORIES:
            return jsonify({'error': 'Invalid story selection'}), 400
        
        # Validate duration
        if not (10 <= data['duration'] <= 25):
            return jsonify({'error': 'Duration must be between 10 and 25 minutes'}), 400
        
        # Validate resolution
        valid_resolutions = ['HD', 'Full HD', '4K']
        if data['resolution'] not in valid_resolutions:
            return jsonify({'error': 'Invalid resolution'}), 400
        
        # Generate job ID
        job_id = str(uuid.uuid4())
        
        # Store job metadata
        job_data = {
            'job_id': job_id,
            'story': data['story'],
            'duration': data['duration'],
            'resolution': data['resolution'],
            'tiktok': data['tiktok'],
            'status': 'queued',
            'progress': 0,
            'created_at': datetime.now().isoformat(),
            'error': None
        }
        
        redis_client.set(f'job:{job_id}', json.dumps(job_data), ex=3600)  # Expire after 1 hour
        
        # Start Celery task
        from tasks import generate_video_task
        generate_video_task.delay(job_id, data)
        
        return jsonify({
            'job_id': job_id,
            'status': 'queued',
            'message': 'Video generation started'
        })
        
    except Exception as e:
        logger.error(f"Error in generate_video: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/status/<job_id>', methods=['GET'])
def get_job_status(job_id):
    """Get job status and progress"""
    try:
        job_data = redis_client.get(f'job:{job_id}')
        if not job_data:
            return jsonify({'error': 'Job not found'}), 404
        
        job_info = json.loads(job_data)
        return jsonify({
            'job_id': job_id,
            'status': job_info['status'],
            'progress': job_info['progress'],
            'created_at': job_info['created_at'],
            'error': job_info.get('error')
        })
        
    except Exception as e:
        logger.error(f"Error in get_job_status: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/download/<job_id>', methods=['GET'])
def download_video(job_id):
    """Download completed video"""
    try:
        job_data = redis_client.get(f'job:{job_id}')
        if not job_data:
            return jsonify({'error': 'Job not found'}), 404
        
        job_info = json.loads(job_data)
        
        if job_info['status'] != 'completed':
            return jsonify({'error': 'Video not ready for download'}), 400
        
        # In production, this would download from S3
        # For now, return the file path
        video_path = f"/tmp/videos/{job_id}.mp4"
        
        if os.path.exists(video_path):
            return send_file(video_path, as_attachment=True, download_name=f"{job_info['story']}.mp4")
        else:
            return jsonify({'error': 'Video file not found'}), 404
        
    except Exception as e:
        logger.error(f"Error in download_video: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)