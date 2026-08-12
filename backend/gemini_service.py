import json
import time
import logging
from typing import List, Dict, Any
import google.generativeai as genai
from google.api_core.exceptions import GoogleAPIError, ResourceExhausted

from backend.config import GEMINI_API_KEY
from backend.models import ClassificationResult

# Configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure the Gemini API client
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-3.1-flash-lite")

PROMPT_TEMPLATE = """You are a hate speech detection model for YouTube comment moderation.

For each comment in the list below, classify it as:
- "Hate Speech"    → abusive language, threats, slurs, discrimination, harassment,
                     or content targeting identity (race, gender, religion, origin)
- "No Hate Speech" → general opinion, criticism, praise, or neutral content

Think step by step for each comment:
1. Does it target a person/group based on identity?
2. Does it contain threats, slurs, or calls to violence?
3. Is the language designed to harass or demean?

Return ONLY a JSON array — one object per comment — in this exact format:
[
  {{
    "comment": "<original comment text>",
    "label": "Hate Speech" | "No Hate Speech",
    "confidence": "High" | "Medium" | "Low",
    "reason": "<one sentence explanation>",
    "type": "Threat" | "Racial/Ethnic" | "Abusive Language" | "Harassment" | "None"
  }}
]

No preamble. No markdown. No explanation. JSON array only.

Few-shot examples:
Input: "People like you should not be allowed to speak publicly. Go back to where you came from."
Output: {{ "label": "Hate Speech", "confidence": "High", "reason": "Xenophobic language targeting the creator's origin.", "type": "Racial/Ethnic" }}

Input: "I will find you and make you regret posting this."
Output: {{ "label": "Hate Speech", "confidence": "High", "reason": "Direct personal threat against the creator.", "type": "Threat" }}

Input: "Disgusting. Your kind is ruining everything."
Output: {{ "label": "Hate Speech", "confidence": "High", "reason": "Dehumanizing language targeting an identity group.", "type": "Abusive Language" }}

Input: "This is the worst video, absolute garbage."
Output: {{ "label": "Hate Speech", "confidence": "Medium", "reason": "Extremely hostile language targeting the creator.", "type": "Abusive Language" }}

Input: "This is overwhelming."
Output: {{ "label": "No Hate Speech", "confidence": "High", "reason": "Expresses personal emotion with no abusive content.", "type": "None" }}

Input: "Good video but too lengthy."
Output: {{ "label": "No Hate Speech", "confidence": "High", "reason": "Constructive feedback with no abusive or hateful content.", "type": "None" }}

Comments to classify:
{comments_json_array}
"""

def clean_json_response(text: str) -> str:
    """Removes markdown code block delimiters if present in the model output."""
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()

def call_gemini_with_backoff(prompt: str) -> str:
    """
    Calls the Gemini API with exponential backoff on rate limit errors.
    Retries up to 3 times (4 attempts total) with delays of 1s, 2s, 4s.
    """
    backoff_delays = [1.0, 2.0, 4.0]
    for attempt, delay in enumerate(backoff_delays + [0.0]):
        try:
            # We explicitly request application/json in the generation config
            response = model.generate_content(
                prompt,
                generation_config={"response_mime_type": "application/json"}
            )
            return response.text
        except (ResourceExhausted, GoogleAPIError) as e:
            # If we've exhausted all backoff delays, raise the error
            if attempt >= len(backoff_delays):
                logger.error("Gemini API call failed after max retries due to rate limit or API error.")
                raise e
            
            # Check if it's a rate limit error (status code 429 or ResourceExhausted)
            logger.warning(
                f"Gemini API rate limit or transient error encountered on attempt {attempt + 1}. "
                f"Retrying in {delay} seconds. Error: {str(e)}"
            )
            time.sleep(delay)
        except Exception as e:
            logger.error(f"Unexpected error during Gemini API call: {str(e)}")
            raise e
    raise GoogleAPIError("Max retries exceeded without successful response")

def classify_batch(comments: List[str]) -> List[ClassificationResult]:
    """
    Classifies a single batch of up to 10 comments.
    Retries once on malformed JSON; falls back to unclassified defaults on second failure.
    """
    comments_json_array = json.dumps(comments, ensure_ascii=False)
    prompt = PROMPT_TEMPLATE.replace("{comments_json_array}", comments_json_array)
    
    fallback_results = [
        ClassificationResult(
            comment=comment,
            label="No Hate Speech",
            confidence="Low",
            reason="Classification failed",
            type="None"
        )
        for comment in comments
    ]
    
    for attempt in range(2):  # Try twice to get a valid parsed JSON response
        try:
            logger.info(f"Classifying batch of {len(comments)} comments (Attempt {attempt + 1})")
            raw_response = call_gemini_with_backoff(prompt)
            cleaned_response = clean_json_response(raw_response)
            
            parsed_data = json.loads(cleaned_response)
            if not isinstance(parsed_data, list):
                raise ValueError("Gemini response is not a JSON list.")
            
            # Align parsed data with the input comments to ensure safety
            results = []
            for i, comment in enumerate(comments):
                # Check if we can extract corresponding index, otherwise fall back for this item
                if i < len(parsed_data) and isinstance(parsed_data[i], dict):
                    item = parsed_data[i]
                    # Ensure all required fields exist, if not let it raise to retry or use fallback
                    results.append(
                        ClassificationResult(
                            comment=comment,  # Keep the exact input comment
                            label=item.get("label", "No Hate Speech"),
                            confidence=item.get("confidence", "Low"),
                            reason=item.get("reason", "Classification failed"),
                            type=item.get("type", "None")
                        )
                    )
                else:
                    results.append(fallback_results[i])
            
            logger.info("Successfully classified batch.")
            return results
            
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            logger.warning(f"Failed to parse Gemini response as valid JSON list: {str(e)}")
            if attempt == 0:
                logger.info("Retrying batch classification once...")
                continue
        except Exception as e:
            logger.error(f"Unexpected classification error on attempt {attempt + 1}: {str(e)}")
            if attempt == 0:
                continue

    # Fallback if both attempts fail
    logger.error("Both classification attempts failed. Returning fallback defaults.")
    return fallback_results

def classify_comments(comments: List[str]) -> List[ClassificationResult]:
    """
    Accepts a list of comment strings, strips blanks, and batches them in groups of 10.
    Returns aggregated ClassificationResult list.
    """
    # Clean and filter input comments
    cleaned_comments = [c.strip() for c in comments if c and c.strip()]
    if not cleaned_comments:
        return []
    
    all_results: List[ClassificationResult] = []
    
    # Process in batches of 10
    batch_size = 10
    for i in range(0, len(cleaned_comments), batch_size):
        batch = cleaned_comments[i:i + batch_size]
        batch_results = classify_batch(batch)
        all_results.extend(batch_results)
        
    return all_results
