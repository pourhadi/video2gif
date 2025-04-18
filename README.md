# Video to GIF Conversion API

This service provides a secure HTTP API to asynchronously convert uploaded videos to GIFs with customizable frames per second (FPS).

## Endpoints

1. **Create Job**  
   **POST** `/jobs`  
   - Headers:  
     - `X-API-KEY`: Your API key  
   - Form data:  
     - `fps` (integer, optional, default `10`): Frames per second for GIF  
     - `file` (file, required): Video file to convert  
   - Returns:  
     ```json
     {
       "job_id": "uuid-string"
     }
     ```
   - Status code: `202 Accepted`

2. **Get Job Status**  
   **GET** `/jobs/{job_id}`  
   - Headers:  
     - `X-API-KEY`: Your API key  
   - Returns:  
     ```json
     {
       "job_id": "uuid-string",
       "status": "queued|processing|finished|failed",
       "download_url": "/jobs/{job_id}/gif" // when finished
       "error": "error message" // when failed
     }
     ```

3. **Download GIF**  
   **GET** `/jobs/{job_id}/gif`  
   - Headers:  
     - `X-API-KEY`: Your API key  
   - Returns: GIF file when job is finished.

## Configuration

- Set environment variable `API_KEY` to secure your endpoints.

## Running with Docker

1. Build the image:  
   ```
   docker build -t video2gif .
   ```
2. Run the container locally:  
   ```
   # Maps host port 8080 to container PORT (default 8080)
   docker run -d --name video2gif -e API_KEY=your_key -p 8080:8080 video2gif
   ```

## Deploying to Google Cloud Run

1. Build and push the container to Google Container Registry:  
   ```
   gcloud builds submit --tag gcr.io/PROJECT_ID/video2gif
   ```

2. Deploy to Cloud Run:  
   ```
   gcloud run deploy video2gif \
     --image gcr.io/PROJECT_ID/video2gif \
     --platform managed \
     --region YOUR_REGION \
     --allow-unauthenticated \
     --set-env-vars API_KEY=your_key
   ```

## Requirements

- Docker
- Video processing is powered by FFmpeg, installed in the container.