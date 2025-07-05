# AI-Generated Bible Story Videos

A full-stack web application that generates AI-powered Bible story videos with narration, images, and video composition.

## Features

- **AI-Generated Content**: Creates scripts, images, voiceovers, and videos using multiple AI services
- **Customizable Options**: Story selection, duration, resolution, and TikTok-optimized format
- **Real-time Progress**: Live progress tracking with WebSocket updates
- **Production Ready**: Docker containerization and cloud deployment configuration

## Architecture

### Backend (Python/Flask)
- **Flask API**: RESTful endpoints for video generation
- **Celery Tasks**: Asynchronous task processing with Redis broker
- **AI Integrations**:
  - OpenAI API for script generation
  - Replicate.com Stable Diffusion for image generation
  - ElevenLabs for voice synthesis
  - FFmpeg for video composition

### Frontend (React/Tailwind CSS)
- **Modern UI**: Responsive design with Tailwind CSS
- **Real-time Updates**: Progress tracking and status polling
- **User Controls**: Story selection, duration, resolution, and format options

### Deployment
- **Backend**: AWS ECS with Docker containers
- **Frontend**: Vercel deployment
- **Storage**: AWS S3 for video files
- **Queue**: Redis for task management

## Setup Instructions

### Prerequisites
- Node.js 18+
- Python 3.9+
- Redis server
- FFmpeg
- Docker (for containerization)

### Environment Variables
Create `.env` files in both backend and frontend directories:

**Backend (.env):**
```
OPENAI_API_KEY=your_openai_key
REPLICATE_API_TOKEN=your_replicate_token
ELEVENLABS_API_KEY=your_elevenlabs_key
REDIS_URL=redis://localhost:6379
AWS_ACCESS_KEY_ID=your_aws_key
AWS_SECRET_ACCESS_KEY=your_aws_secret
S3_BUCKET_NAME=your_s3_bucket
```

**Frontend (.env):**
```
REACT_APP_API_URL=http://localhost:5000
```

### Local Development

1. **Backend Setup:**
```bash
cd backend
pip install -r requirements.txt
redis-server
celery -A app.celery worker --loglevel=info
flask run
```

2. **Frontend Setup:**
```bash
cd frontend
npm install
npm start
```

### Docker Deployment

```bash
docker-compose up --build
```

## API Endpoints

- `POST /generate` - Start video generation
- `GET /status/<job_id>` - Check job status
- `GET /download/<job_id>` - Download completed video

## Technologies Used

- **Backend**: Flask, Celery, Redis, OpenAI, Replicate, ElevenLabs, FFmpeg
- **Frontend**: React, Tailwind CSS, Axios
- **Deployment**: Docker, AWS ECS, Vercel
- **Storage**: AWS S3

## License

MIT License