# YouTube Hate Speech Detector Prototype

A prototype application that takes raw comment strings, classifies them as "Hate Speech" or "No Hate Speech" using Google Gemini 1.5 Pro, and displays categorized results dynamically inside a Streamlit web interface.

## Project Structure

```text
hate-speech-detector/
├── backend/
│   ├── config.py            # Configuration and Env verification
│   ├── models.py            # Pydantic v2 schemas
│   ├── gemini_service.py    # Batching and Gemini API service logic
│   └── main.py              # FastAPI application configuration
├── frontend/
│   └── app.py               # Streamlit interactive UI layout
├── .env.example             # Template for API Key configuration
├── requirements.txt         # Python project dependencies
└── README.md                # Documentation instructions
```

## Setup Instructions

### 1. Configure the Environment
Create a `.env` file in the root directory by copying the example template:
```bash
cp .env.example .env
```
Open `.env` and fill in your Gemini API Key:
```text
GEMINI_API_KEY=AIzaSy...your_gemini_api_key_here
```

### 2. Install Dependencies
Ensure you have Python 3.9+ installed. Set up a virtual environment and install the required modules:
```bash
python -m venv venv
# On Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# On Windows (CMD):
.\venv\Scripts\activate.bat
# On macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
```

### 3. Run the FastAPI Backend
Start the backend server on `http://localhost:8000`:
```bash
uvicorn backend.main:app --reload
```

### 4. Run the Streamlit Frontend
In a new terminal window (with the virtual environment activated), start the frontend server:
```bash
streamlit run frontend/app.py
```
This automatically opens the app in your browser at `http://localhost:8501`.

---

## API Usage & Verification

### GET /health
Check backend server readiness:
```bash
curl -X GET http://localhost:8000/health
```
Response:
```json
{
  "status": "ok"
}
```

### POST /classify
Submit batch comments for classification:
```bash
curl -X POST http://localhost:8000/classify \
  -H "Content-Type: application/json" \
  -d '{"comments": ["This is overwhelming.", "Disgusting. Your kind is ruining everything."]}'
```

### Example Input & Output JSON
**Request:**
```json
{
  "comments": [
    "I love the visuals of this video!",
    "I will find you and make you regret posting this."
  ]
}
```

**Response:**
```json
{
  "total": 2,
  "hate_speech_count": 1,
  "results": [
    {
      "comment": "I love the visuals of this video!",
      "label": "No Hate Speech",
      "confidence": "High",
      "reason": "General positive criticism and praise for video visual aesthetics.",
      "type": "None"
    },
    {
      "comment": "I will find you and make you regret posting this.",
      "label": "Hate Speech",
      "confidence": "High",
      "reason": "Direct violent threat targeting the publisher.",
      "type": "Threat"
    }
  ]
}
```
