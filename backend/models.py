from typing import Literal
from pydantic import BaseModel, Field

class CommentRequest(BaseModel):
    comments: list[str] = Field(
        ...,
        min_length=1,
        max_length=100,
        description="A list of raw comment strings to analyze. Must contain between 1 and 100 comments."
    )

class ClassificationResult(BaseModel):
    comment: str = Field(..., description="The original comment text analyzed.")
    label: Literal["Hate Speech", "No Hate Speech"] = Field(..., description="The classification result.")
    confidence: Literal["High", "Medium", "Low"] = Field(..., description="Confidence level of classification.")
    reason: str = Field(..., description="One-sentence explanation of classification logic.")
    type: Literal["Threat", "Racial/Ethnic", "Abusive Language", "Harassment", "None"] = Field(
        ...,
        description="Category/type of hate speech if detected, or None."
    )

class ClassificationResponse(BaseModel):
    total: int = Field(..., description="Total number of comments analyzed.")
    hate_speech_count: int = Field(..., description="Number of hate speech comments detected.")
    results: list[ClassificationResult] = Field(..., description="List of classification results.")
