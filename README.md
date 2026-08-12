# YouTube Hate Speech Detector

An AI-powered application that classifies YouTube comments as **Hate Speech** or **No Hate Speech**, helping creators, social media managers, and community moderators cut through manual comment review at scale.

## Problem

Manually moderating hundreds or thousands of YouTube comments is time-consuming and emotionally draining. YouTube's native spam filters don't offer granular hate speech detection, leaving creators without visibility into toxic engagement patterns — resulting in delayed moderation, unmoderated harmful content, and reputational risk.

## Solution

This project accepts raw comments via a REST API and classifies each one using **Google Gemini**, giving creators fast, data-driven moderation insight without needing to read every comment themselves.

## Repository Structure

This repo contains two parallel backend implementations plus a shared Streamlit UI:

```
hate_speech_detector/
├── backend/            # Python backend
├── frontend/            # Streamlit UI — comment input & classification results
└── java_backend/
    └── hate-speech-detector/
        ├── src/main/java/com/mari/hatespeechdetector/
        │   ├── config/       # Gemini API & CORS configuration
        │   ├── controller/   # REST endpoints
        │   ├── dto/          # Request/response DTOs (Lombok)
        │   └── service/      # Gemini integration & classification logic
        ├── src/test/java/com/mari/hatespeechdetector/
        └── pom.xml
```

- **`backend/`** — Python implementation of the classification service
- **`java_backend/hate-speech-detector/`** — Spring Boot 3 implementation of the same service (`com.mari.hatespeechdetector`)
- **`frontend/`** — Streamlit app that sends comments to whichever backend is active and displays classification results

> Note: The two backends are alternate implementations of the same API, not dependent on each other. Point the Streamlit frontend at whichever one you're running.

## Tech Stack

| Layer | Technology |
|---|---|
| Java Backend | Spring Boot 3, Java, Maven |
| Python Backend | Python |
| Frontend | Streamlit |
| AI Engine | Google Gemini (`gemini-3.1-flash-lite`) |
| HTTP Client (Java) | OkHttp3 (v4.12.0) |
| API Docs (Java) | SpringDoc OpenAPI 2.5 (Swagger UI) |
| DTOs (Java) | Lombok |

## Key Design Decisions

- Comments are submitted directly via API request body (no YouTube Data API dependency)
- Batched Gemini calls — 10 comments per request — for efficiency
- Exponential backoff (1s → 2s → 4s) for rate-limit resilience
- Constructor injection over field injection (Java service)
- Gemini model name externalized as a config constant, not hardcoded

## Target Users

- **YouTube Content Creators** — monitor and manage toxic comments without hours of manual review
- **Social Media Managers** — maintain a healthy comment community for brands and organizations
- **Community Moderators** — prioritize and action flagged comments efficiently on large channels

## Sample Classification

| Comment | Classification |
|---|---|
| "People like you should not be allowed to speak publicly. Go back to where you came from." | Hate Speech |
| "I will find you and make you regret posting this." | Hate Speech |
| "This is overwhelming" | No Hate Speech |
| "Good video but too lengthy" | No Hate Speech |

## Getting Started

### Java Backend
```bash
cd java_backend/hate-speech-detector
mvn spring-boot:run
```
Swagger UI: `http://localhost:8080/swagger-ui.html` (adjust port if configured differently)

### Python Backend
```bash
cd backend
pip install -r requirements.txt
python app.py
```

### Streamlit Frontend
```bash
cd frontend
pip install -r requirements.txt
streamlit run app.py
```

> Update the requirements/run commands above to match your actual entry point and dependency files.

## Status

🚧 Prototype in active development.
