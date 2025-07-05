from celery import Celery
import os
import json
import redis
import openai
import replicate
from elevenlabs import generate, save, set_api_key
import boto3
from datetime import datetime
import logging
import subprocess
import time
from PIL import Image
import requests
from io import BytesIO

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Celery
celery = Celery('tasks', broker=os.getenv('REDIS_URL', 'redis://localhost:6379'))

# Initialize Redis client
redis_client = redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379'))

# Initialize AI services
openai.api_key = os.getenv('OPENAI_API_KEY')
set_api_key(os.getenv('ELEVENLABS_API_KEY'))

# AWS S3 client
s3_client = boto3.client(
    's3',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
)

def update_job_progress(job_id, status, progress, error=None):
    """Update job progress in Redis"""
    try:
        job_data = redis_client.get(f'job:{job_id}')
        if job_data:
            job_info = json.loads(job_data)
            job_info['status'] = status
            job_info['progress'] = progress
            if error:
                job_info['error'] = error
            job_info['updated_at'] = datetime.now().isoformat()
            redis_client.set(f'job:{job_id}', json.dumps(job_info), ex=3600)
    except Exception as e:
        logger.error(f"Error updating job progress: {str(e)}")

def generate_script(story, duration, tiktok_format=False):
    """Generate script using OpenAI API"""
    try:
        # Adjust script based on format
        format_instruction = "short-form, engaging TikTok" if tiktok_format else "detailed narrative"
        
        prompt = f"""
        Create a {format_instruction} script for a {duration}-minute video about the Bible story: {story}.
        
        Requirements:
        - Duration: {duration} minutes
        - Format: {'TikTok/short-form' if tiktok_format else 'Traditional narrative'}
        - Include scene descriptions for image generation
        - Include timing cues for each scene
        - Engaging and educational content
        - Family-friendly language
        
        Structure your response as JSON with this format:
        {{
            "title": "Story Title",
            "scenes": [
                {{
                    "scene_number": 1,
                    "duration": 30,
                    "narration": "Text to be spoken",
                    "image_description": "Detailed description for image generation",
                    "timing_start": 0,
                    "timing_end": 30
                }}
            ]
        }}
        """
        
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a biblical storyteller creating engaging video scripts."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=2000,
            temperature=0.7
        )
        
        script_content = response.choices[0].message.content
        
        # Parse JSON response
        try:
            script_data = json.loads(script_content)
            return script_data
        except json.JSONDecodeError:
            # Fallback parsing if JSON is malformed
            return {
                "title": story,
                "scenes": [{
                    "scene_number": 1,
                    "duration": duration * 60,
                    "narration": script_content,
                    "image_description": f"Biblical scene depicting {story}",
                    "timing_start": 0,
                    "timing_end": duration * 60
                }]
            }
            
    except Exception as e:
        logger.error(f"Error generating script: {str(e)}")
        raise

def generate_images(scenes, resolution):
    """Generate images using Replicate Stable Diffusion"""
    try:
        generated_images = []
        
        # Resolution mapping
        resolution_map = {
            'HD': '1280x720',
            'Full HD': '1920x1080',
            '4K': '3840x2160'
        }
        
        dimensions = resolution_map.get(resolution, '1920x1080')
        
        for i, scene in enumerate(scenes):
            try:
                # Enhanced prompt for biblical scenes
                enhanced_prompt = f"""
                Biblical art style, {scene['image_description']}, 
                cinematic composition, warm lighting, ancient Middle Eastern setting,
                highly detailed, dramatic atmosphere, religious art style,
                no text, family-friendly content
                """
                
                # Use Replicate's Stable Diffusion
                output = replicate.run(
                    "stability-ai/stable-diffusion:27b93a2413e7f36cd83da926f3656280b2931564ff050bf9575f1fdf9bcd7478",
                    input={
                        "prompt": enhanced_prompt,
                        "negative_prompt": "inappropriate content, violence, scary, dark",
                        "width": int(dimensions.split('x')[0]),
                        "height": int(dimensions.split('x')[1]),
                        "num_inference_steps": 50,
                        "guidance_scale": 7.5,
                        "scheduler": "K_EULER"
                    }
                )
                
                # Download and save image
                image_url = output[0] if isinstance(output, list) else output
                response = requests.get(image_url)
                
                if response.status_code == 200:
                    image_path = f"/tmp/images/scene_{i+1}.png"
                    os.makedirs("/tmp/images", exist_ok=True)
                    
                    with open(image_path, 'wb') as f:
                        f.write(response.content)
                    
                    generated_images.append({
                        'scene_number': scene['scene_number'],
                        'image_path': image_path,
                        'duration': scene['duration']
                    })
                    
                    logger.info(f"Generated image for scene {i+1}")
                else:
                    raise Exception(f"Failed to download image for scene {i+1}")
                    
            except Exception as e:
                logger.error(f"Error generating image for scene {i+1}: {str(e)}")
                # Use placeholder image
                generated_images.append({
                    'scene_number': scene['scene_number'],
                    'image_path': None,
                    'duration': scene['duration']
                })
        
        return generated_images
        
    except Exception as e:
        logger.error(f"Error generating images: {str(e)}")
        raise

def generate_voiceover(script_data):
    """Generate voiceover using ElevenLabs"""
    try:
        audio_files = []
        
        for i, scene in enumerate(script_data['scenes']):
            try:
                # Generate audio for each scene
                audio = generate(
                    text=scene['narration'],
                    voice="Adam",  # Using Adam voice as specified
                    model="eleven_multilingual_v2"
                )
                
                # Save audio file
                audio_path = f"/tmp/audio/scene_{i+1}.wav"
                os.makedirs("/tmp/audio", exist_ok=True)
                
                save(audio, audio_path)
                
                audio_files.append({
                    'scene_number': scene['scene_number'],
                    'audio_path': audio_path,
                    'duration': len(audio) / 22050  # Approximate duration
                })
                
                logger.info(f"Generated voiceover for scene {i+1}")
                
            except Exception as e:
                logger.error(f"Error generating voiceover for scene {i+1}: {str(e)}")
                audio_files.append({
                    'scene_number': scene['scene_number'],
                    'audio_path': None,
                    'duration': scene['duration']
                })
        
        return audio_files
        
    except Exception as e:
        logger.error(f"Error generating voiceover: {str(e)}")
        raise

def stitch_video(script_data, images, audio_files, resolution, tiktok_format, output_path):
    """Stitch together video using FFmpeg"""
    try:
        # Create temporary video segments
        os.makedirs("/tmp/video_segments", exist_ok=True)
        
        # Resolution settings
        resolution_map = {
            'HD': '1280x720',
            'Full HD': '1920x1080',
            '4K': '3840x2160'
        }
        
        dimensions = resolution_map.get(resolution, '1920x1080')
        aspect_ratio = "9:16" if tiktok_format else "16:9"
        
        # Create video segments for each scene
        segment_paths = []
        
        for i, scene in enumerate(script_data['scenes']):
            try:
                image_path = next((img['image_path'] for img in images if img['scene_number'] == scene['scene_number']), None)
                audio_path = next((audio['audio_path'] for audio in audio_files if audio['scene_number'] == scene['scene_number']), None)
                
                if image_path and audio_path and os.path.exists(image_path) and os.path.exists(audio_path):
                    segment_path = f"/tmp/video_segments/segment_{i+1}.mp4"
                    
                    # FFmpeg command to create video segment
                    cmd = [
                        'ffmpeg', '-y',
                        '-loop', '1',
                        '-i', image_path,
                        '-i', audio_path,
                        '-c:v', 'libx264',
                        '-c:a', 'aac',
                        '-b:a', '192k',
                        '-pix_fmt', 'yuv420p',
                        '-shortest',
                        '-vf', f'scale={dimensions}:force_original_aspect_ratio=increase,crop={dimensions}',
                        segment_path
                    ]
                    
                    result = subprocess.run(cmd, capture_output=True, text=True)
                    
                    if result.returncode == 0:
                        segment_paths.append(segment_path)
                        logger.info(f"Created video segment {i+1}")
                    else:
                        logger.error(f"FFmpeg error for segment {i+1}: {result.stderr}")
                        
            except Exception as e:
                logger.error(f"Error creating video segment {i+1}: {str(e)}")
        
        # Concatenate all segments
        if segment_paths:
            # Create file list for FFmpeg concat
            concat_file = "/tmp/concat_list.txt"
            with open(concat_file, 'w') as f:
                for segment_path in segment_paths:
                    f.write(f"file '{segment_path}'\n")
            
            # Final concatenation command
            cmd = [
                'ffmpeg', '-y',
                '-f', 'concat',
                '-safe', '0',
                '-i', concat_file,
                '-c', 'copy',
                output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info("Video stitching completed successfully")
                return True
            else:
                logger.error(f"FFmpeg concatenation error: {result.stderr}")
                return False
        else:
            logger.error("No video segments to concatenate")
            return False
            
    except Exception as e:
        logger.error(f"Error stitching video: {str(e)}")
        return False

@celery.task
def generate_video_task(job_id, request_data):
    """Main task to generate video"""
    try:
        logger.info(f"Starting video generation for job {job_id}")
        
        # Extract parameters
        story = request_data['story']
        duration = request_data['duration']
        resolution = request_data['resolution']
        tiktok_format = request_data['tiktok']
        
        # Step 1: Generate script (20% progress)
        update_job_progress(job_id, 'processing', 10)
        logger.info(f"Generating script for {story}")
        script_data = generate_script(story, duration, tiktok_format)
        update_job_progress(job_id, 'processing', 20)
        
        # Step 2: Generate images (40% progress)
        logger.info("Generating images")
        images = generate_images(script_data['scenes'], resolution)
        update_job_progress(job_id, 'processing', 40)
        
        # Step 3: Generate voiceover (60% progress)
        logger.info("Generating voiceover")
        audio_files = generate_voiceover(script_data)
        update_job_progress(job_id, 'processing', 60)
        
        # Step 4: Stitch video (80% progress)
        logger.info("Stitching video")
        os.makedirs("/tmp/videos", exist_ok=True)
        output_path = f"/tmp/videos/{job_id}.mp4"
        
        success = stitch_video(script_data, images, audio_files, resolution, tiktok_format, output_path)
        
        if success:
            update_job_progress(job_id, 'processing', 90)
            
            # Step 5: Upload to S3 (if configured)
            if os.getenv('S3_BUCKET_NAME'):
                try:
                    s3_client.upload_file(output_path, os.getenv('S3_BUCKET_NAME'), f"videos/{job_id}.mp4")
                    logger.info("Video uploaded to S3")
                except Exception as e:
                    logger.error(f"Error uploading to S3: {str(e)}")
            
            # Complete job
            update_job_progress(job_id, 'completed', 100)
            logger.info(f"Video generation completed for job {job_id}")
            
        else:
            update_job_progress(job_id, 'failed', 0, 'Video stitching failed')
            logger.error(f"Video generation failed for job {job_id}")
        
    except Exception as e:
        logger.error(f"Error in video generation task: {str(e)}")
        update_job_progress(job_id, 'failed', 0, str(e))