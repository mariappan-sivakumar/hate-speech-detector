import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from backend.models import CommentRequest, ClassificationResponse
from backend.gemini_service import classify_comments

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="YouTube Hate Speech Detector API",
    description="FastAPI backend to detect hate speech in YouTube comments using Google Gemini Pro",
    version="1.0.0"
)

# Enable CORS for localhost Streamlit (default port 8501)
origins = [
    "http://localhost:8501",
    "http://127.0.0.1:8501",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/classify", response_model=ClassificationResponse)
async def classify(request: CommentRequest):
    logger.info(f"Received request to classify {len(request.comments)} comments")
    
    # Process classification
    results = classify_comments(request.comments)
    
    # Aggregate results
    total = len(results)
    hate_speech_count = sum(1 for r in results if r.label == "Hate Speech")
    
    response = ClassificationResponse(
        total=total,
        hate_speech_count=hate_speech_count,
        results=results
    )
    
    logger.info(f"Successfully processed request. Total: {total}, Hate Speech: {hate_speech_count}")
    return response

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled exception occurred: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"error": f"Internal Server Error: {str(exc)}"}
    )
